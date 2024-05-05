import discord
from discord.ext import tasks, commands
import datetime
from web3 import Web3, HTTPProvider
import contract_abi

# Blockchain information
contract_address     = "0x53f370d68e0d8f58ef587f7fb8552f6207de3a3a"
wallet_private_key   = ""
wallet_address       = "0x136e2D86cd870b75e81Ff88A9F6DaDeC5A33c39f"
contract_address = Web3.to_checksum_address(contract_address)

#Set up contract
w3 = Web3(HTTPProvider(""))
contract = w3.eth.contract(address = contract_address, abi = contract_abi.abi)
addresses = {}

# Initialize contract for the first time
# tx = contract.functions.initialize().build_transaction({'nonce': w3.eth.get_transaction_count(wallet_address), 'gas':10000000})
# signed_txn = w3.eth.account.sign_transaction(tx, private_key=wallet_private_key)
# result = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

# Bot token
bot_token = ""

# Set up bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='?',  intents=intents)


# Read messages every 30 minutes and grant tokens
@tasks.loop(minutes=30.0) 
async def read_messages():
    # Get test server
    for guild in bot.guilds:
        if guild.id == 1236456999437471864:
            authors = {}
            now = datetime.datetime.now()
            # Get all text channels
            for channel in guild.channels:
                if channel.type == discord.ChannelType.text and channel.name != 'bot-commands':

                    # Get 200 most recent messages
                    messages = [message async for message in channel.history(limit=200)]
                    for message in messages:
                        score = 1
                        message_time = message.created_at.timestamp()
                        
                        # Ignore messages not in last 30 minutes or from bot
                        if message_time > (now - datetime.timedelta(minutes=30)).timestamp():
                            if message.author != bot.user:

                                # Add points to users
                                for reaction in message.reactions:
                                    if reaction.emoji == '👎':
                                        score -= (reaction.count - int(message.author in [user async for user in reaction.users()]))
                                    elif reaction.emoji == '👍':
                                        score += (reaction.count - int(message.author in [user async for user in reaction.users()]))
                                if message.author.global_name in authors:
                                    authors[message.author.global_name] += score
                                else:
                                    authors[message.author.global_name] = score

                    # Commit points to blockchain
            await guild.get_channel(1236752365693042729).send("Sending money:")
            for person in authors.keys():
                if person in addresses:
                    await guild.get_channel(1236752365693042729).send(str(person) + " " + str(authors[person]))
                    if authors[person] < 0:
                        balance = contract.functions.balanceOf(addresses[person]).call()
                        brdata = contract.functions.burn(addresses[person], min(balance, authors[person]*-1)).build_transaction({'nonce': w3.eth.get_transaction_count(wallet_address),'gas':10000000})
                        signed_txn = w3.eth.account.sign_transaction(brdata, private_key=wallet_private_key)
                        result = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                        try:
                            w3.eth.wait_for_transaction_receipt(result)
                        except:
                            await guild.get_channel(1236752365693042729).send("Transaction timed out")
                    else:
                        mdata = contract.functions.mint(addresses[person], authors[person]).build_transaction({'nonce': w3.eth.get_transaction_count(wallet_address),'gas':10000000})
                        signed_txn = w3.eth.account.sign_transaction(mdata, private_key=wallet_private_key)
                        result = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                        # result = w3.eth.send_transaction(mdata)
                        try:
                            w3.eth.wait_for_transaction_receipt(result)
                        except:
                            await guild.get_channel(1236752365693042729).send("Transaction timed out")


# Polling command  Usage: ?poll question
# Yes no support only   
@bot.command()
async def poll(ctx, *, reason):
    if ctx.channel.name == "bot-commands":
        message = await ctx.guild.get_channel(1236752365693042729).send("POLL: " + reason + "\nYes: 0\nNo: 0")
        await message.add_reaction('👍')
        await message.add_reaction('👎')

# Payment command Useage: ?pay @recipient amount
@bot.command()
async def pay(ctx, user, amount):
    if ctx.channel.name == "bot-commands":
        if amount.isnumeric() and ctx.message.mentions:
            await ctx.send("Sending " + user + " " + amount)
            balance = contract.functions.balanceOf(addresses[ctx.author.global_name]).call()
            if balance < int(amount):
                await ctx.send("Invalid Balance")
                return
            brdata = contract.functions.transfer(addresses[ctx.message.mentions[0].global_name], addresses[ctx.author.global_name], int(amount)).build_transaction({'nonce': w3.eth.get_transaction_count(wallet_address),'gas':10000000})
            signed_txn = w3.eth.account.sign_transaction(brdata, private_key=wallet_private_key)
            result = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            try:
                w3.eth.wait_for_transaction_receipt(result)
            except:
                await ctx.send("Transaction timed out")
        else:
            await ctx.send("Error using command. Usage: ?pay @recipient amount")

# Function to spend tokens on polls
@bot.event
async def on_reaction_add(reaction, user):
    now = datetime.datetime.now()

    # Only look for valid reacts on recent polls
    if reaction.emoji in '👍👎' and user != bot.user and reaction.message.created_at.timestamp() > (now - datetime.timedelta(minutes=30)).timestamp():
        if reaction.message.author == bot.user and "POLL:" in reaction.message.content:

            # DM user asking for amount to spend
            await user.send("How much would you like to spend?")

            # Process user response
            try:
                msg = await bot.wait_for('message', check = lambda x: x.channel == user.dm_channel and x.author == user, timeout=120)

                # Update user balance and vote totals
                if msg.content.isnumeric():
                    await user.send("Spending " + msg.content + " tokens")

                    # Send transaction to blockchain
                    balance = contract.functions.balanceOf(addresses[user.global_name]).call()
                    if balance < int(msg.content):
                        await user.send("Invalid Balance")
                        return
                    brdata = contract.functions.burn(addresses[user.global_name],int(msg.content)).build_transaction({'nonce': w3.eth.get_transaction_count(wallet_address),'gas':10000000})
                    signed_txn = w3.eth.account.sign_transaction(brdata, private_key=wallet_private_key)
                    result = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    try:
                        w3.eth.wait_for_transaction_receipt(result)
                    except:
                        await user.get_channel(1236752365693042729).send("Transaction timed out")

                    # Update votes
                    text = reaction.message.content.split("\n")
                    if reaction.emoji == '👎':
                        await reaction.message.edit(content=text[0] +"\n" + text[1] +"\nNo: "+ str(int(text[2].replace("No: ", ""))+int(msg.content))) 
                    else:
                        await reaction.message.edit(content=text[0] +"\nYes: " +str(int(text[1].replace("Yes: ", ""))+int(msg.content))+"\n" + text[2]) 
            except:
                await user.send("There was an error")

#Verify with etherium address
@bot.command()
async def verify(ctx, addr):
    if ctx.channel.name == "bot-commands":
        addresses[ctx.author.global_name] = addresses
        with open("addresses.txt", "a") as f:
            f.write(ctx.author.global_name +" " + addr + "\n")
        await ctx.send("Verified address")
 
# Check balance
@bot.command()
async def bal(ctx):
    if ctx.author.global_name in addresses:
        await ctx.send(contract.functions.balanceOf(addresses[ctx.author.global_name]).call())        
    else:
        await ctx.send("Please add an address") 
        print(addresses)

@bot.event
async def on_ready():
    with open("addresses.txt") as f:
        for line in f:
            items = line.strip().split(" ")
            addresses[items[0]] = items[1]
    print(f'We have logged in as {bot.user}')
    read_messages.start()  # You start the task here.

bot.run(bot_token)
