# Project Spec

Project: Simple LLM Agent to Call a Restaurant 
Goal: Build a small end-to-end demo where the user gives a restaurant-related request, the LLM understands the task, triggers a basic call action through a tool or MCP, and returns the result. Restaurant details such as name and phone number are already available, so the demo only focuses on intent understanding, action triggering, and result summary. 

Example:
User says: Call this restaurant and ask if they have a table for 2 tonight at 7 PM. 
The system: reads the request extracts the task details calls a tool or MCP action gets the result, returns a short summary 

Scope: For this demo, support only a few simple requests: ask for table availability ask whether the restaurant is open. Considering that the restaurant name and phone number are already given by the system, so no restaurant search is needed. 
Stretch goal: Do restaurant information search on the fly.

