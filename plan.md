## What are we building

We are building an Notes app for AI agents.

## The Plan

So the core idea is a user can chat with claude web and if he needs some expertise of chatgpt so he says hey store the summary of this session in the notes app then he goes to chatgpt and reference this session and ask it to do what he wanted to do like generating an image which claude can't do.

So the whole thing is managed by HTTP MCP server.

The Database itself is designed like a graph, the initial chat is considered as node-1 and then the consecutive chats are considered as node-n. There will be a node 0 which will be a summary of all the nodes inside it. Which DB would be better Postgres or Neo4j ?

This is gonna be multiple user application but for managing and authenticating the user will use Clerk

Tools for the MCP server:

1. Save the node: takes in the content, and reference ID which can be null. If the reference is null then its considered as node-1 and a node-0 is also created and both of them are connected. Node-0 is content is populated only when the user calls the Root summarizer prompt. If the reference is not null, then it just becomes the child node of the parent.

2. Retrieve the node : It takes in the node id and returns the summary of that node.

3. Delete the node: It takes in the node id and delete it and the subsequent child nodes.

There will be three prompt offered by the MCP server. An Summarizer prompt, A Root Summarizer, A Retriever and a How to .

1. Summarizer Prompt: This tells the AI app how to summarize the chat and then call the MCP tool required to store the summary in the db.The prompt should summarize only the current chat not the previous ones, and make sure to not distill the information to much. The summary should be based on the current chat session. It can say " we looked at this in the previous session" but not too much.

2. The Root Summarizer: Summarizing the whole graph is this prompts job. We could have done this with mcp sampling but since Claude desktop doesn't support it will go with a two step tool calling the first tool gets all the chats then ask claude to summarize it and send it to a second tool that saves it.

3. The Retriever Prompt: The Retriever returns the node0 summary which contains the reference to other sections with their title and the summary of the node given. So title should also be descriptive not something random. The node0 summary can be something that's non descriptive. The Retriever prompt also mentions that this is a summary came from such a application and if you want to go deeper into any of the referenced docs it can use the retriever tool to retrieve that content.

4. How to Prompt: Just tells the user how to use this application.

## Database:

A node object will contain: A title, tag (claude app, claude code, etc), summary (markdown format), parent references, child references, the actual chat link, id, child references.

A root node will not have a parent reference. A child can't have multiple parents but a parent can have multiple child.

If we are going with postgres then a link table that connects the nodes

I am not sure if the root node should be a separate table or the same table with a boolean ?

## UI

The mockups are at [./assets/mockup](file:///D:/Projects/ai-notes/assets/mockup)

We manage the login and signup using clerk, the homepage just contains a search box with the latest 10 root nodes listed by default.

In the content page, we show the full graph in the root content page and in all the consecutive pages we show the child and parent reference node ids.

## Tech stack

We are gonna use FastAPI with the official mcp sdk for the backend and for the frontend we are gonna use React + Vite with tailwindv4 for styling.

For Auth we are gonna use Clerk

For Auth with the mcp client too we are gonna use Clerk. They support CIMD so will just use that.

## Moving forward

Will move phase by phase, and building the UI will be at the end of the phase

I think this order makes sense but open to suggestions:

1. Setup the fastapi server and mount the mcp server and setup the DB, If we are going with postgres will use SQLmodel with alembic
2. Setup the auth for both the api and mcp client
3. Implement the tools and the prompts
4. Test it with claude code as mcp client
5. Implement the frontend
