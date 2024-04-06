import discord
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timedelta
import json
import arrow

intents = discord.Intents.all()  # Enable all intents for member tracking
token = os.environ.get('TOKEN')
prefix = "!"

bot = commands.Bot(command_prefix=prefix, intents=intents)
bot_list = ['<@1203539615865114634>','<@1204295916732022834>']


BD_Alive = False
BD_Time = datetime.utcnow()
current_date = arrow.utcnow().date()
CA_Shift = arrow.get(current_date).replace(hour=22, minute=0, second=0)

async def get_timers():

    global BD_Alive
    global BD_Time
    
    # Specify the URL to scrape
    url = 'https://pirateking.online/database/portal/'

    # Use Selenium to wait for JavaScript to load dynamic content
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait for dynamic content to load (you may need to adjust the timeout)
    driver.implicitly_wait(10)

    # Get the page source after JavaScript has executed
    page_source = driver.page_source

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract the timer value based on the HTML structure
    timer_element = soup.find('span', class_='boss-time-3-3')
    timer_text = timer_element.text.strip()
    # Close the Selenium WebDriver
    driver.quit()

    if timer_text == '':
        BD_Time = datetime.utcnow()
        BD_Alive = True
        return

    numbers_only = re.sub(r'\D', '', timer_text)
    if len(numbers_only) == 7:
        hours = int(numbers_only[:3])
        minutes = int(numbers_only[3:5])
        seconds = int(numbers_only[5:])
    else:
        hours = int(numbers_only[:2])
        minutes = int(numbers_only[2:4])
        seconds = int(numbers_only[4:])

    BD_Time = datetime.utcnow() + timedelta(hours=hours, minutes=minutes, seconds=seconds)
    BD_Alive = False



@bot.event
async def on_ready():
    await get_timers()
    print(f'Logged in as {bot.user.name}')


#ADD OR REMOVE MEMBERS    

@bot.command(name='add')
async def add_members(ctx):

  message = ctx.message
  content = message.content.lower()
  
  if ctx.message.author == ctx.bot.user.id:
    return
  
  if (ctx.message.author.guild_permissions.administrator or 
      ctx.message.author.id == 307640466638110721 or 
      ctx.message.author.id == 706869141700608101):
    pass
  else:
    await ctx.send("Only admins can use this command.")
    return

  new_people = content[len('!add'):].strip()
  
  if new_people.startswith("<@"):

    #step 1
    try:
      msg_referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except AttributeError:
      await ctx.author.send("You have to tag a bot list message.")
      await message.delete()
      return
    
    if(msg_referenced.author.id != ctx.bot.user.id):
      await ctx.author.send("I only edit lists made by <@{}>.".format(ctx.bot.user.id))
      await message.delete()
      return

    if not msg_referenced.content.startswith("Players List"):
      await ctx.author.send("You have to reference to a list message made by <@{}>.".format(ctx.bot.user.id))
      await message.delete()
      return
    
    add_list = [user.mention for user in message.mentions]
    add_list = list(set(add_list)-set(bot_list))
    
    msg_referenced = await ctx.fetch_message(ctx.message.reference.message_id)
    existing_people= [user.mention for user in msg_referenced.mentions]
    new_list = list(set(existing_people) | set(add_list))

    #step 3
    new_list = "Players List (" + str(len(new_list)) + " members):\n\n" + "\n".join(new_list)
    await msg_referenced.edit(content=new_list)

  else:
      await ctx.author.send("Wrong syntax. Use `!add @user1 @user2`")
  await message.delete()

@bot.command(name='remove')
async def remove_members(ctx):
    
    message = ctx.message
    content = message.content.lower()
    
    if ctx.message.author == ctx.bot.user.id:
       return

    if (ctx.message.author.guild_permissions.administrator or 
        ctx.message.author.id == 307640466638110721 or 
        ctx.message.author.id == 706869141700608101):
      pass
    else:
      await ctx.author.send("Only admins can use this command.")
      await message.delete()
      return
    
    if content[len(',remove'):].strip().startswith("<@"):

      #step 1
      try:
        msg_referenced = await ctx.fetch_message(ctx.message.reference.message_id)
      except AttributeError:
        await ctx.author.send("You have to tag a bot list message.")
        await message.delete()
        return

      if(msg_referenced.author.id != ctx.bot.user.id):
        await ctx.author.send("I only edit lists made by <@{}>.".format(ctx.bot.user.id))
        await message.delete()
        return

      if not msg_referenced.content.startswith("Players List"):
        await ctx.author.send("You have to reference to a list message made by <@{}>.".format(ctx.bot.user.id))
        await message.delete()
        return

      remove_list = [user.mention for user in message.mentions]
      
      msg_referenced = await ctx.fetch_message(ctx.message.reference.message_id)
      existing_people= [user.mention for user in msg_referenced.mentions]
      new_list = [item for item in existing_people if item not in remove_list]

      #step 3
      new_list = "Players List (" + str(len(new_list)) + " members):\n\n" + "\n".join(new_list)
      await msg_referenced.edit(content=new_list)

    else:
      await ctx.author.send("Wrong syntax. Use `!remove @user1 @user2`")
    await message.delete()


#Making List

@bot.command(name='list')
async def list_members(ctx):
    message = ctx.message
    # Check if the command is invoked in a voice channel
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel

        # Get the members in the voice channel
        channel_members = [member for member in voice_channel.members if not member.bot]

        if channel_members:
            # Create a list of usernames with their tags
             user_ids_and_tags = [member.mention for member in channel_members]
             user_list = chr(10).join(user_ids_and_tags)
            
        await ctx.send(f'Players List ({len(user_ids_and_tags)} members):\n\n{user_list}')
    else:
        await ctx.author.send('You are not in a voice channel.')
    await message.delete()

#Delete bot message

@bot.command(name='del')
async def delmsg(ctx):

  message = ctx.message
  content = message.content.lower()
  
  if ctx.message.author == ctx.bot.user.id:
    return
  
  if (ctx.message.author.guild_permissions.administrator or 
      ctx.message.author.id == 307640466638110721 or 
      ctx.message.author.id == 706869141700608101):
    pass
  else:
    await ctx.author.send("Only admins can use this command.")
    return
  try:
      msg_referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
  except AttributeError:
      await ctx.author.send("You have to tag a bot message.")
      return
  if(msg_referenced.author.id != ctx.bot.user.id):
      await ctx.author.send("I only edit lists made by <@{}>.".format(ctx.bot.user.id))
      return

  await msg_referenced.delete()
  await message.delete()


#MAZE TIMERS

#BD

@bot.command(name='bd')
async def scrape_url(ctx):
    
    global BD_Alive
    global BD_Time
    
    try:
        time_left = BD_Time - datetime.utcnow()
        
        if time_left < timedelta(seconds=1):
            timer_text = await get_timers()
            if BD_Alive == True:
                await ctx.send('**BD is Alive! Go go go**')
                return
            else:
                time_left = BD_Time - datetime.utcnow()

        
        future_time_epoch = int(BD_Time.timestamp())

        # Calculate the total seconds
        total_seconds = time_left.total_seconds()

        # Calculate days, hours, minutes, and seconds
        days_float, remainder = divmod(total_seconds, 86400)
        hours_float, remainder = divmod(remainder, 3600)
        minutes_float, seconds_float = divmod(remainder, 60)

        days = int(days_float)
        hours = int(hours_float)
        minutes = int(minutes_float)
        seconds = int(seconds_float)

        # Calculate the date and time from the current time in UTC
        
        if days == 0: formatted_timer = f'{days:02}d {hours:02}h {minutes:02}m {seconds:02}s'
        else: formatted_timer = f'{days:02}d {hours:02}h {minutes:02}m'

        # Send the calculated date and time to the Discord channel
        await ctx.send(f'**BD Will Spawn in**: {formatted_timer} \n Tap or hover for local time --> <t:{future_time_epoch}:R>')

    except Exception as e:
        await ctx.send(f'An error occurred: {e}')

#FC

@bot.command(name='fc')
async def fc(ctx):

  if ctx.message.author == ctx.bot.user.id:
    return

  current_time_utc = arrow.utcnow()
  current_date = current_time_utc.date()
  fix_time = arrow.get(current_date).replace(hour=0, minute=0, second=0)
  hrs = 0
  shift_time = fix_time
  shift_time2= shift_time.shift(hours=1)

  while hrs<=24: 
    if shift_time <= current_time_utc <= shift_time2:
        await ctx.send (f'FC Open. Closes <t:{int(shift_time2.timestamp())}:R>')
    elif shift_time2 <= current_time_utc <= shift_time.shift(hours=4):
        await ctx.send (f'FC Closed. Next open <t:{int(shift_time.shift(hours=4).timestamp())}:R> ({shift_time.shift(hours=4).format("HH:mm")} UTC)')

    hrs+=4
    shift_time=fix_time.shift(hours=hrs)
    shift_time2= shift_time.shift(hours=1)

#DS

@bot.command(name='ds')
async def ds(ctx):

  if ctx.message.author == ctx.bot.user.id:
    return

  current_time_utc = arrow.utcnow()
  current_date = current_time_utc.date()
  fix_time = arrow.get(current_date).replace(hour=1, minute=0, second=0)
  hrs = 0
  shift_time = fix_time
  shift_time2= shift_time.shift(hours=1)

  while hrs<=24: 
    if shift_time <= current_time_utc <= shift_time2:
        await ctx.send (f'DS Open. Closes <t:{int(shift_time2.timestamp())}:R>')
    elif shift_time2 <= current_time_utc <= shift_time.shift(hours=4):
        await ctx.send (f'DS Closed. Next open <t:{int(shift_time.shift(hours=4).timestamp())}:R> ({shift_time.shift(hours=4).format("HH:mm")} UTC)')

    hrs+=4
    shift_time=fix_time.shift(hours=hrs)
    shift_time2= shift_time.shift(hours=1)


#DW

@bot.command(name='dw')
async def dw(ctx):

  if ctx.message.author == ctx.bot.user.id:
    return

  current_time_utc = arrow.utcnow()
  current_date = current_time_utc.date()
  fix_time = arrow.get(current_date).replace(hour=2, minute=0, second=0)
  hrs = 0
  shift_time = fix_time
  shift_time2= shift_time.shift(minutes=40)

  while hrs<=24: 
    if shift_time <= current_time_utc <= shift_time2:
        await ctx.send (f'DW Open. Closes <t:{int(shift_time2.timestamp())}:R>')
    elif shift_time2 <= current_time_utc <= shift_time.shift(hours=4):
        await ctx.send (f'DW Closed. Next open <t:{int(shift_time.shift(hours=4).timestamp())}:R> ({shift_time.shift(hours=4).format("HH:mm")} UTC)')

    hrs+=4
    shift_time=fix_time.shift(hours=hrs)
    shift_time2= shift_time.shift(minutes=40) 

# Run the bot
bot.run(token)
