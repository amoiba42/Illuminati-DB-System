# Project Phase 4 – Team 53

## Team Members

- Raunak Seksaria (2023113019)
- Vishesh Saraswat (2023111001)
- Harshit Lalwani (2023111028)
- Gracy Garg (2023101118)

Video link is [here](https://iiitaphyd-my.sharepoint.com/:v:/g/personal/vishesh_saraswat_research_iiit_ac_in/ESZEqQvJFjtPiWQ9gREgsXgBbb5h1M4J3MxyLuR_GzkBzQ?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=Chrg8e)

## Available Operations

### Retrieval Operations
1. **View Sacred Timeline Events by Illuminati Member**
   - Retrieves all events orchestrated by a specific Illuminati member
   - Shows event details including date, time, status, and description

2. **View Factions by Member Count**
   - Lists factions with more than specified number of members
   - Shows faction details including aim, symbol, and head member
   - Member count is dynamically calculated from Faction_Members table

3. **View Member Statistics**
   - Displays comprehensive membership statistics across all factions
   - Shows total members, average per faction

4. **Search Artifacts by Power**
   - Search for artifacts based on their mystical powers
   - Displays artifact details including origin, procurement date, and guards

5. **Generate Monthly Faction Report**
   - Comprehensive report of faction activities for a specific month
   - Shows meetings, attendance, and hierarchical structure

6. **Analyze Surveillance Targets**
   - Statistical analysis of surveillance operations
   - Breaks down targets by type (Individual/Organization)
   - Shows geographical and temporal distribution of operations

### Modification Operations
7. **Add New Faction Member**
   - Add members to factions with unique member IDs within factions
   - Supports hierarchical structure with leader assignments

8. **Update Sanctum Sanctorum Location**
   - Modify the location details of Illuminati's secret sanctums
   - Updates street, city, and country information

9. **Delete Artifact Record**
   - Remove destroyed artifacts from the database
   - Handles cascading deletions of related records

10. **Update Key Illuminati Member Name**
    - Modify the name of existing Illuminati members
    - Maintains historical records and relationships

11. **Change Faction Head Title**
    - Update the leadership structure of factions
    - Ensures proper authority chain maintenance

