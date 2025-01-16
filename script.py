import pymysql
from datetime import datetime
import os
from dateutil import parser
from typing import List, Dict, Any, Tuple

class IlluminatiDB:
    def __init__(self):
        self.connection = pymysql.connect(
            host='localhost',
            user='root',
            password='mysql',
            database='Illuminati',
            cursorclass=pymysql.cursors.DictCursor
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def get_timeline_events_by_member(self, member_title: str) -> List[Dict]:
        with self.connection.cursor() as cursor:
            query = """
            SELECT ste.*, kim.Name as Member_Name
            FROM Sacred_Timeline_Events ste
            JOIN Orchestrates o ON ste.Event_Id = o.Event_Id
            JOIN Key_Illuminati_Members kim ON o.Title = kim.Title
            WHERE o.Title = %s
            """
            cursor.execute(query, (member_title,))
            return cursor.fetchall()

    def get_factions_by_member_count(self, min_members: int) -> List[Dict]:
        with self.connection.cursor() as cursor:
            query = """
            SELECT
                f.Faction_Id,
                f.Aim,
                f.Symbol,
                kim.Name as Head_Name,
                COUNT(fm.Member_Id) as Member_Count
            FROM Factions f
            LEFT JOIN Faction_Members fm ON f.Faction_Id = fm.Faction_Id
            LEFT JOIN Key_Illuminati_Members kim ON f.HeadTitle = kim.Title
            GROUP BY f.Faction_Id
            HAVING Member_Count > %s
            ORDER BY Member_Count DESC
            """
            cursor.execute(query, (min_members,))
            return cursor.fetchall()

    def get_total_members(self) -> Dict[str, int]:
        with self.connection.cursor() as cursor:
            query = """
            SELECT
                COUNT(DISTINCT Member_Id) as total_members,
                COUNT(DISTINCT Faction_Id) as total_factions,
                ROUND(COUNT(DISTINCT Member_Id) / COUNT(DISTINCT Faction_Id), 2) as avg_members_per_faction
            FROM Faction_Members
            """
            cursor.execute(query)
            return cursor.fetchone()

    def search_artifacts_by_power(self, power_text: str) -> List[Dict]:
        with self.connection.cursor() as cursor:
            query = """
            SELECT DISTINCT
                at.Artifact_Id,
                at.Origin,
                at.Date_Of_Procurement,
                p.Power,
                f.Aim as Controlling_Faction,
                COUNT(DISTINCT g.Member_Id) as Guard_Count
            FROM Artifacts_And_Treasures at
            JOIN Powers p ON at.Artifact_Id = p.Artifact_Id
            LEFT JOIN Factions f ON at.Faction_Id = f.Faction_Id
            LEFT JOIN Guards g ON at.Artifact_Id = g.Artifact_Id
            WHERE p.Power LIKE %s
            GROUP BY at.Artifact_Id, at.Origin, at.Date_Of_Procurement, f.Aim, p.Power
            """
            cursor.execute(query, (f"%{power_text}%",))
            return cursor.fetchall()

    def generate_monthly_faction_report(self, year: int, month: int) -> Dict[str, Any]:
        with self.connection.cursor() as cursor:
            meetings_query = """
            SELECT 
                f.Faction_Id,
                f.Aim,
                fm.Date,
                fm.Time,
                fm.Agenda,
                fm.City,
                fm.Country,
                COUNT(DISTINCT fmem.Member_Id) as Member_Count,
                kim.Name as Faction_Head
            FROM Faction_Meetings fm
            JOIN Factions f ON fm.Faction_Id = f.Faction_Id
            LEFT JOIN Faction_Members fmem ON f.Faction_Id = fmem.Faction_Id
            LEFT JOIN Key_Illuminati_Members kim ON f.HeadTitle = kim.Title
            WHERE YEAR(fm.Date) = %s AND MONTH(fm.Date) = %s
            GROUP BY f.Faction_Id, f.Aim, fm.Date, fm.Time, fm.Agenda, fm.City, fm.Country, kim.Name
            ORDER BY fm.Date, fm.Time
            """
            cursor.execute(meetings_query, (year, month))
            meetings = cursor.fetchall()

            hierarchy_query = """
            WITH RECURSIVE MemberHierarchy AS (
                -- Base case: top-level leaders (no Leader_Id)
                SELECT 
                    Member_Id,
                    Fname,
                    Lname,
                    Faction_Id,
                    Leader_Id,
                    0 as Level
                FROM Faction_Members
                WHERE Leader_Id IS NULL
                
                UNION ALL
                
                -- Recursive case: members with leaders
                SELECT 
                    fm.Member_Id,
                    fm.Fname,
                    fm.Lname,
                    fm.Faction_Id,
                    fm.Leader_Id,
                    mh.Level + 1
                FROM Faction_Members fm
                JOIN MemberHierarchy mh ON fm.Leader_Id = mh.Member_Id
            )
            SELECT 
                mh.Member_Id,
                mh.Fname,
                mh.Lname,
                mh.Faction_Id,
                mh.Leader_Id,
                mh.Level,
                f.Aim as Faction_Name,
                (SELECT COUNT(*)
                FROM Faction_Members sub
                WHERE sub.Leader_Id = mh.Member_Id) as Subordinates
            FROM MemberHierarchy mh
            JOIN Factions f ON mh.Faction_Id = f.Faction_Id
            ORDER BY mh.Faction_Id, mh.Level, mh.Member_Id
            """
            cursor.execute(hierarchy_query)
            hierarchy = cursor.fetchall()

            return {
                "meetings": meetings,
                "hierarchy": hierarchy
            }
    def analyze_surveillance_targets(self) -> Dict[str, Any]:
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    COUNT(DISTINCT Nationality) as unique_nationalities,
                    COUNT(DISTINCT Current_Location) as unique_locations
                FROM Individuals
            """)
            individual_stats = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    COUNT(DISTINCT Type) as unique_types,
                    COUNT(DISTINCT President) as unique_presidents
                FROM Organizations
            """)
            org_stats = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s.Surveillance_Id) as total_surveillance_ops,
                    COUNT(DISTINCT sur.Title) as active_surveillors,
                    MIN(s.Start_Date_Of_Survey) as earliest_surveillance,
                    MAX(s.Start_Date_Of_Survey) as latest_surveillance
                FROM Surveillance s
                LEFT JOIN Surveys sur ON s.Surveillance_Id = sur.Surveillance_Id
            """)
            summary = cursor.fetchone()

            return {
                "individuals": individual_stats,
                "organizations": org_stats,
                "summary": summary
            }

    def add_faction_member(self, member_data: Dict) -> bool:
        try:
            with self.connection.cursor() as cursor:
                check_query = """
                SELECT Member_Id
                FROM Faction_Members
                WHERE Member_Id = %s
                """
                cursor.execute(check_query, (member_data['Member_Id'],))
                if cursor.fetchone():
                    raise ValueError("Member ID already exists")

                faction_query = "SELECT Faction_Id FROM Factions WHERE Faction_Id = %s"
                cursor.execute(faction_query, (member_data['Faction_Id'],))
                if not cursor.fetchone():
                    raise ValueError("Invalid Faction ID")

                if member_data.get('Leader_Id'):
                    leader_query = """
                    SELECT Member_Id
                    FROM Faction_Members
                    WHERE Member_Id = %s AND Faction_Id = %s
                    """
                    cursor.execute(leader_query, (member_data['Leader_Id'], member_data['Faction_Id']))
                    if not cursor.fetchone():
                        raise ValueError("Invalid Leader ID or Leader not in same faction")

                insert_query = """
                INSERT INTO Faction_Members
                (Member_Id, Fname, Mname, Lname, Dob, Faction_Id, Leader_Id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    member_data['Member_Id'],
                    member_data['Fname'],
                    member_data.get('Mname'),
                    member_data['Lname'],
                    member_data['Dob'],
                    member_data['Faction_Id'],
                    member_data.get('Leader_Id')
                ))
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_sanctum_location(self, mantra: str, new_location: Dict) -> bool:
        try:
            with self.connection.cursor() as cursor:
                check_query = "SELECT Mantra FROM Sanctum_Sanctorum WHERE Mantra = %s"
                cursor.execute(check_query, (mantra,))
                if not cursor.fetchone():
                    raise ValueError("Sanctum not found")

                update_query = """
                UPDATE Sanctum_Sanctorum
                SET Street = %s, City = %s, Country = %s
                WHERE Mantra = %s
                """
                cursor.execute(update_query, (
                    new_location['Street'],
                    new_location['City'],
                    new_location['Country'],
                    mantra
                ))
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            raise e

    def delete_artifact(self, artifact_id: int) -> bool:
        try:
            with self.connection.cursor() as cursor:
                check_query = """
                SELECT a.*, f.Aim as Faction_Name
                FROM Artifacts_And_Treasures a
                JOIN Factions f ON a.Faction_Id = f.Faction_Id
                WHERE a.Artifact_Id = %s
                """
                cursor.execute(check_query, (artifact_id,))
                artifact = cursor.fetchone()
                if not artifact:
                    raise ValueError("Artifact not found")

                cursor.execute("DELETE FROM Powers WHERE Artifact_Id = %s", (artifact_id,))
                cursor.execute("DELETE FROM Guards WHERE Artifact_Id = %s", (artifact_id,))
                cursor.execute("DELETE FROM Perform_Rituals WHERE Artifact_Id = %s", (artifact_id,))
                cursor.execute("DELETE FROM Artifacts_And_Treasures WHERE Artifact_Id = %s", (artifact_id,))

                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            raise e
    def update_illuminati_name(self, title: str, new_name: str) -> bool:
        """Update: Change the name of a Key Illuminati Member"""
        try:
            with self.connection.cursor() as cursor:
                # First verify member exists
                cursor.execute("SELECT Title FROM Key_Illuminati_Members WHERE Title = %s", (title,))
                if not cursor.fetchone():
                    raise ValueError("Illuminati member not found")

                update_query = """
                UPDATE Key_Illuminati_Members
                SET Name = %s
                WHERE Title = %s
                """
                cursor.execute(update_query, (new_name, title))
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_faction_head(self, faction_id: int, new_head_title: str) -> bool:
        """Update: Change the HeadTitle of a Faction"""
        try:
            with self.connection.cursor() as cursor:
                # Verify faction exists
                cursor.execute("SELECT Faction_Id FROM Factions WHERE Faction_Id = %s", (faction_id,))
                if not cursor.fetchone():
                    raise ValueError("Faction not found")
                
                # Verify new head title exists in Key_Illuminati_Members
                cursor.execute("SELECT Title FROM Key_Illuminati_Members WHERE Title = %s", (new_head_title,))
                if not cursor.fetchone():
                    raise ValueError("New head title not found in Key Illuminati Members")

                update_query = """
                UPDATE Factions
                SET HeadTitle = %s
                WHERE Faction_Id = %s
                """
                cursor.execute(update_query, (new_head_title, faction_id))
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            raise e


def print_menu():
    print("\n=== 🔺 Illuminati Database Management System 🔺 ===")
    print("\nRetrieval Operations:")
    print("1. View Sacred Timeline events by Illuminati Member")
    print("2. View factions by member count")
    print("3. View total members across all factions")
    print("4. Search artifacts by power")
    print("5. Generate monthly faction report")
    print("6. Analyze surveillance targets")

    print("\nModification Operations:")
    print("7. Add new faction member")
    print("8. Update Sanctum Sanctorum location")
    print("9. Delete artifact record")
    print("10. Update Key Illuminati Member name")
    print("11. Change Faction Head Title")


    print("\n0. Exit")
    print("\n============================================")

def get_user_input(prompt: str, data_type=str):
    """Get and validate user input"""
    while True:
        try:
            user_input = input(prompt)
            if data_type == bool:
                return user_input.lower() in ['y', 'yes']
            return data_type(user_input)
        except ValueError:
            print(f"Invalid input. Please enter a valid {data_type.__name__}")
def main():
    try:
        with IlluminatiDB() as db:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_menu()
                choice = input("\nEnter your choice (0-9): ")

                try:
                    if choice == '0':
                        print("\nExiting the Illuminati Database System... 👁️")
                        break

                    elif choice == '1':
                        member_title = input("\nEnter Illuminati Member Title: ")
                        events = db.get_timeline_events_by_member(member_title)
                        print(f"\n=== Sacred Timeline Events for {member_title} ===")
                        for event in events:
                            print(f"\nEvent ID: {event['Event_Id']}")
                            print(f"Date: {event['Date']}")
                            print(f"Time: {event['Time']}")
                            print(f"Status: {event['Status']}")
                            print(f"Description: {event['Description']}")

                    elif choice == '2':
                        min_members = get_user_input("\nEnter minimum number of members: ", int)
                        factions = db.get_factions_by_member_count(min_members)
                        print(f"\n=== Factions with more than {min_members} members ===")
                        for faction in factions:
                            print(f"\nFaction ID: {faction['Faction_Id']}")
                            print(f"Aim: {faction['Aim']}")
                            print(f"Symbol: {faction['Symbol']}")
                            print(f"Total Members: {faction['Member_Count']}")
                            print(f"Head: {faction['Head_Name']}")

                    elif choice == '3':
                        stats = db.get_total_members()
                        print("\n=== Faction Membership Statistics ===")
                        print(f"Total Members: {stats['total_members']}")
                        print(f"Total Factions: {stats['total_factions']}")
                        print(f"Average Members per Faction: {stats['avg_members_per_faction']}")

                    elif choice == '4':
                        power = input("\nEnter power to search for: ")
                        artifacts = db.search_artifacts_by_power(power)
                        print("\n=== Artifacts ===")
                        last_id = None
                        for artifact in artifacts:
                            if last_id != artifact['Artifact_Id']:
                                print(f"\nArtifact ID: {artifact['Artifact_Id']}")
                                print(f"Origin: {artifact['Origin']}")
                                print(f"Procurement Date: {artifact['Date_Of_Procurement']}")
                                print(f"Controlling Faction: {artifact['Controlling_Faction']}")
                                print(f"Number of Guards: {artifact['Guard_Count']}")
                                print("Powers:")
                                last_id = artifact['Artifact_Id']
                            print(f"  - {artifact['Power']}")

                    elif choice == '5':
                        year = get_user_input("Enter year (YYYY): ", int)
                        month = get_user_input("Enter month (1-12): ", int)
                        report = db.generate_monthly_faction_report(year, month)
                        
                        print("\n=== Monthly Faction Report ===")
                        print("\nMeetings:")
                        for meeting in report['meetings']:
                            print(f"\nFaction: {meeting['Aim']}")
                            print(f"Date: {meeting['Date']}")
                            print(f"Time: {meeting['Time']}")
                            print(f"Location: {meeting['City']}, {meeting['Country']}")
                            print(f"Agenda: {meeting['Agenda']}")
                            print(f"Member Count: {meeting['Member_Count']}")
                            print(f"Faction Head: {meeting['Faction_Head']}")

                        print("\nHierarchy:")
                        current_faction = None
                        for member in report['hierarchy']:
                            if current_faction != member['Faction_Id']:
                                current_faction = member['Faction_Id']
                                print(f"\nFaction: {member['Faction_Name']}")
                            
                            indent = "  " * member['Level']
                            print(f"{indent}└─ {member['Fname']} {member['Lname']}")
                            print(f"{indent}   Level: {member['Level']}")
                            print(f"{indent}   Subordinates: {member['Subordinates']}")

                    elif choice == '6':
                        analysis = db.analyze_surveillance_targets()
                        print("\n=== Surveillance Analysis ===")
                        
                        print("\nIndividual Targets:")
                        print(f"Total Count: {analysis['individuals']['count']}")
                        print(f"Unique Nationalities: {analysis['individuals']['unique_nationalities']}")
                        print(f"Unique Locations: {analysis['individuals']['unique_locations']}")
                        
                        print("\nOrganization Targets:")
                        print(f"Total Count: {analysis['organizations']['count']}")
                        print(f"Unique Types: {analysis['organizations']['unique_types']}")
                        print(f"Unique Presidents: {analysis['organizations']['unique_presidents']}")
                        
                        print("\nSurveillance Summary:")
                        print(f"Total Operations: {analysis['summary']['total_surveillance_ops']}")
                        print(f"Active Surveillors: {analysis['summary']['active_surveillors']}")
                        print(f"Earliest Operation: {analysis['summary']['earliest_surveillance']}")
                        print(f"Latest Operation: {analysis['summary']['latest_surveillance']}")
                    elif choice == '7':
                        print("\n=== Add New Faction Member ===")
                        member_data = {
                            'Member_Id': get_user_input("Enter Member ID: ", int),
                            'Fname': input("Enter First Name: "),
                            'Mname': input("Enter Middle Name (press Enter to skip): ") or None,
                            'Lname': input("Enter Last Name: "),
                            'Dob': input("Enter Date of Birth (YYYY-MM-DD): "),
                            'Faction_Id': get_user_input("Enter Faction ID: ", int),
                            'Leader_Id': get_user_input("Enter Leader ID (0 for none): ", int) or None
                        }
                        if db.add_faction_member(member_data):
                            print("Member added successfully!")

                    elif choice == '8':
                        print("\n=== Update Sanctum Sanctorum Location ===")
                        mantra = input("Enter Sanctum Mantra: ")
                        new_location = {
                            'Street': input("Enter new street address: "),
                            'City': input("Enter new city: "),
                            'Country': input("Enter new country: ")
                        }
                        if db.update_sanctum_location(mantra, new_location):
                            print("Location updated successfully!")

                    elif choice == '9':
                        artifact_id = get_user_input("\nEnter Artifact ID to delete: ", int)
                        confirm = input("Are you sure you want to delete this artifact? (y/n): ")
                        if confirm.lower() == 'y':
                            if db.delete_artifact(artifact_id):
                                print("Artifact deleted successfully!")
                        else:
                            print("Deletion cancelled.")

                    elif choice == '10':
                        print("\n=== Update Key Illuminati Member Name ===")
                        title = input("Enter member's Title: ")
                        new_name = input("Enter new name: ")
                        if db.update_illuminati_name(title, new_name):
                            print("Name updated successfully!")

                    elif choice == '11':
                        print("\n=== Change Faction Head Title ===")
                        faction_id = get_user_input("Enter Faction ID: ", int)
                        new_head_title = input("Enter new Head Title: ")
                        if db.update_faction_head(faction_id, new_head_title):
                            print("Faction head updated successfully!")

                    else:
                        print("\nInvalid choice. Please try again.")

                except Exception as e:
                    print(f"\nError: {str(e)}")

                input("\nPress Enter to continue...")

    except Exception as e:
        print(f"Database connection error: {str(e)}")

if __name__ == "__main__":
    main()
