
PROJECT NAME : IT Incident Auto-Triage & Tracker [ Mini Project 3  ]

Name - Bhola Roy : B7_Orsu_Venkata_Saikiran_Incident_Tracker_MiniProject_3
Open The Terminal 
------------------------------------------------------------------------------------------

How to run the Project

1. Open the Project Folder in VS Code 

2. Make Sure Python 3.x is installed.

3. Open The Terminal 
    Then -- cd incident_tracker
    Then -- python main.py

4. Now Go to Ouput --> report.html --> ( right click ) open with live server



---------------------------------------------------------------------------------------------


Files in use

*  data/incidents.json — input data file.
*  output/report.html — final HTML report.
*  output/report.json — JSON summary report.



Config File

Here,  
   MOCK_API == True     {The project runs in mock mode, noo real API account is needed.}


   //else we can use
   MOCK_API == FALSE for connecting API//


---------------------------------------------------------------------------------------------

 IN THIS PROJECT
 
 Loads 12 incidents from a JSON file  -->  Classifies each incident type using regex -->
 Assigns severity level based on keywords --> Raises mock tickets on ServiceNow, Jira, and Azure Boards --> Then Produces a final HTML  report

---------------------------------------------------------------------------------------------