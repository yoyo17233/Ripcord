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

## Snoopie Fact Cog

- /snoopiefact           => Sends a snapple style fact to whichever discord server the command was sent in
- /gemini                => Uses gemini API to ask a question to the AI
- /sendallsnoopiefact    => Sends a snapple style fact to every discord server the bot is in that has a valid channel (Locked to bot admins - which is only me at the moment)
Automatically sends a sendallsnoopiefact every day at 10am - as long as the bot is running

## Role + Channel Setting Cog

- /setmcpermsrole        => Set the role that can use the minecraft commands
- /setmcconsolepermsrole => Set the role that can use the minecraft console commands
- /setmcconsolechannel   => Set the channel for Minecraft console messages
- /setmcchatchannel      => Set the channel for Minecraft chat messages
- /setmcbotchannel       => Set the channel for the Minecraft bot messages
- /setfactchannel        => Set the channel for Snoopie facts
- /setfactrole           => Set the role to ping for Snoopie facts
- /setpermsrole          => Set the role to have Snoopie fact permissions

Questions can be brought to timothy.kwartler@gmail.com or yoyo.4444 on discord