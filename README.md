# YeetBot
A bot for the Yeet Discord Server

Hey, this is a personal bot I'm mainly using for my Discord and Minecraft server, to combine functionality between them, however it also has some other features. Many values are stored via config to persist through bot lifetimes. Feel free to change things to get them to work for your server. There exists functionality for one machine to host multiple servers concurrently for multiple servers as well, with additional ports/discord servers etc.

If you end up using this bot and you think its neat, feel free to send me a couple of bucks <3 https://buymeacoffee.com/yoyo4444

In order to be able to use the bot, set up the .env using the .env.example file, and then you first need to set up the roles + channels that you want (If you don't want the fun facts at 10am, just don't set the factchannel) If you have any issues setting it up, feel free to message me on discord: yoyo.4444

Additionally, you must name the servers that each discord server has access to via: "ServerList":["Oceanblock2","Skies2","SkyFactory5","WPIEsports"] in the config. These names should be the exact names of the folder of the server.

## Minecraft Server Cog

- /start                 => Remotely starts the currently selected server (User must have minecraft permission discord role)
- /stop                  => Remotely stops whichever server is currently running
- /restart               => Stops the current server, and starts the currently selected server (most often, this is going to be the same selection)
- /server                => "-" parameter displays current selected server, otherwise, server dropdown changes selected server
- /ping                  => Bot will respond "Pong" to ensure bot is online
- /status                => Will give the status of the server, if one is up or not
- /list                  => Runs the /list command in minecraft, and prints the result
- /tps                   => Runs /forge tps or /neoforge tps to get server performance values
- /say <message>         => Says the message in chat as [Rcon]

## Role + Channel Setting Cog

- /createcontainer       - Creates a container to hold a server
    * Bot Perm -> Permission to use the bot
    * Console Perm -> Permission to use the console
    * Nick -> Nickname for the container
    * Bot Channel -> Channel to give commands to the bot (Implicit from the channel where the command is run)
    * Chat Channel -> Channel for minecraft chat
    * Console Channel -> Channel for minecraft chat
    * Port -> Port for minecraft server to run on
- /container             - Shows information on any container
- /allowserver           - Allows current container to swap to this server (servers automatically grabbed from directory in .env)

Questions can be brought to timothy.kwartler@gmail.com or yoyo.4444 on discord