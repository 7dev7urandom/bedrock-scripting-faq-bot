import json
import os
import time
import datetime

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

# was going to use the commands lib, but personally I find it easier to use the discord.Client() instead



def loadConfig():
    default_config = {
        'allow_bug_reports': False,
        'bug_report_cooldown': 300
    }
    if not os.path.exists( os.path.join( os.getcwd(), 'config.json' ) ):
        json.dump( default_config, open(os.path.join( os.getcwd(), 'config.json' ),'w'), indent=4 )
    config_json = json.load( open(os.path.join( os.getcwd(), 'config.json' ),'r') )
    for key in default_config:
        if not key in config_json:
            config_json[key] = default_config[key]
    return config_json

CONFIG = loadConfig()

def dumpConfig():
    json.dump( CONFIG, open(os.path.join( os.getcwd(), 'config.json' ),'w'), indent=4 )



class BOT_DATA:

    BOT_COMMAND_PREFIX = '!'
    # the string that the bot recognises as a command
    FAQ_QUERY_PREFIX = '?'
    # the string that the bot recognises as a FAQ query

    TOKEN_FILENAME = 'token.txt'
    # the filename of the txt file where the bot token is stored



    FAQ_DATA_FILENAME = 'faq.json'
    FAQ_DATA_FILENAME_BIN = 'faq_bin.json'



    FAQ_MANAGEMENT_ROLE = 'faq-management'
    # the role that can manage the faqs
    BOT_ADMIN_ROLE = 'bsb-admin'
    # the role that can manage the faqs

    COMMAND_PREFIXES = {
        'bug': 'bug',
        'help': 'help',
        'faq_viewing': 'faq',
        'faq_management': 'fm'
    }
    # the command prefixes that the bot recognises

    FAQ_MANAGEMENT_COMMANDS = {
        'list': ['list', 'all', 'faqs'],
        'add': ['add', 'create', 'new', 'make'],
        'delete': ['delete', 'remove', 'incinerate', 'shred'],
        'edit': ['edit', 'change', 'modify'],
        'recycle': ['recycle', 'bin', 'faq-bin'],

        'bug-report-enabled': ['r-enabled', 'enable-reporting', 'bug-report'],
        'bug-report-cooldown': ['r-cooldown', 'reporting-cooldown', 'bug-report-cooldown']
    }

    PAGINATE_FAQ_LIST = 5

    BLACKLISTED_TAGS = ['list']

    try: BUG_REPORT_CHANNEL_ID = int(open(os.path.join(os.getcwd(),'bugreportchannelID.txt'),'r').readline().strip())
    except: print("ERROR READING bugreportchannelID.txt"); BUG_REPORT_CHANNEL_ID = 0

    BUG_REPORT_SPAM_DELAY = CONFIG['bug_report_cooldown']
    # delay (in seconds) between bug reports by users
    ALLOW_BUG_REPORTS = CONFIG['allow_bug_reports'] if BUG_REPORT_CHANNEL_ID != 0 else False









'''
this is just a simple function to take large list and
split it into a list of sub-lists of no more than size n
'''
def paginate_list(l,n):
    '''Returns l (list) paginated to pages of n (int) size'''
    return [l[i:i+n] for i in range(0,len(l),n)]



'''
this function just loads the json data from the FAQ file,
then returns it
'''
def loadFaqFile():
    '''Returns the faq data read from the faq json file'''
    return json.load(open( os.path.join(os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME) , 'r'))

'''
this function dumps a dict into the FAQ file
'''
def dumpFaqFile(faq):
    '''Writes faq (json data) to the faq json file'''
    json.dump(faq, open( os.path.join(os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME) , 'w'), indent=4)

def addFaq(new_faq):
    '''Adds a FAQ to the faq data, and then dumps the faq data to the faq json file'''
    faq_data['faq_data'].append(new_faq)
    faq_data['faq_data'] = sorted( faq_data['faq_data'], key=lambda faq: faq['title'] )
    dumpFaqFile(faq_data)

def deleteFaq(faq_tag):
    '''Delete a FAQ from the faq data, and then dumps the faq data to the faq json file'''
    faq = findFaqByTag(faq_tag)
    if faq == None: return

    
    if not os.path.exists( os.path.join( os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME_BIN ) ):
        open(os.path.join( os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME_BIN ), 'w').write( json.dumps([],indent=4) )
    
    backup = json.load( open(os.path.join( os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME_BIN ), 'r') )
    backup.append(faq)
    open(os.path.join( os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME_BIN ), 'w').write( json.dumps(backup,indent=4) )

    faq_data['faq_data'].remove(faq)
    dumpFaqFile(faq_data)

def findFaqByTag(faq_tag):
    '''Returns the faq found by tag, if no FAQ exists, returns None'''
    found = list( [ x for x in faq_data['faq_data'] if faq_tag in x['tag'] ] )
    if len(found) == 0: return None
    return found[0]

def searchFaqByTag(faq_tag):
    '''Returns the faq found by tag, otherwise tries to search for FAQ, otherwise returns None'''
    found = list( [ x for x in faq_data['faq_data'] if faq_tag in x['tag'] ] )
    if len(found) == 0:
        # if no FAQ was found, search for it by looking through titles

        distances = []
        contains_tag_in_title = None
        contains_tag_in_info = None

        for faq in faq_data['faq_data']:
            for tag in faq['tag']:
                distance = 100 - fuzz.ratio( tag, faq_tag )
                if distance < 75:
                    distances.append( [distance, faq] )
            if faq_tag.replace('-',' ').lower() in faq['title'].lower():
                contains_tag_in_title = faq
                distances.append( [55, faq] )
            if faq_tag.replace('-',' ').lower() in faq['info'].lower():
                contains_tag_in_info = faq
                distances.append( [65, faq] )
        
        sorted_distances = sorted( distances, key=lambda i: i[0], reverse=False )

        if len(sorted_distances) > 0:
            return sorted_distances[0][1]

        return contains_tag_in_title or contains_tag_in_info or None

    return found[0]

'''
this function just flattens a list
'''
flatten = lambda l: [item for sublist in l for item in sublist]

def getValidAliases(aliases):
    '''Returns a list of all the aliases from the current list that aren't already part of other FAQs'''
    current_aliases = flatten( list( [f['tag'] for f in faq_data['faq_data']] ) )
    v = list([a for a in aliases if (not a in current_aliases) and (not a in BOT_DATA.BLACKLISTED_TAGS)])
    return v

def check(author, channel):
    '''Runs a check to confirm message author'''
    def inner_check(message):
        return message.author == author and message.channel == channel
    return inner_check




BUG_REPORTS_BY_USERS = {}




# client = commands.Bot(command_prefix = BOT_DATA.BOT_COMMAND_PREFIX)
client = discord.Client()


@client.event
async def on_ready():
    print(f"Logged into discord as {client}")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"the chat .. {BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.COMMAND_PREFIXES['help']}"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    author = message.author
    try:
        roles = author.roles
    except:
        roles = []
    channel = message.channel


    if isinstance(channel, discord.channel.DMChannel):
        # await channel.send("I don't execute commands in DMs, sorry")
        # don't execute commands in DMs
        return
    


    if message.content == f'{BOT_DATA.BOT_COMMAND_PREFIX}ping':
        # a debug message - listen for !ping
        await channel.send('pong!')
    


    if message.content.startswith(BOT_DATA.BOT_COMMAND_PREFIX):
        # check that this message is a command, e.g: '!help'

        print(f"[DEBUG] command called : {message.content}")

        command_request = message.content.split( BOT_DATA.BOT_COMMAND_PREFIX, 1 )[-1]
        if command_request:
            # make sure the user didn't just type nothing
            
            command_split = command_request.split(' ')
            main_command = command_split[0]



            if main_command == BOT_DATA.COMMAND_PREFIXES['bug'] and not CONFIG['allow_bug_reports']:
                '''
                the user wants to report a bug, but bug reports are turned off
                '''
                embed = discord.Embed(
                    title = '',
                    description = f'''\
**Bug report response**
Bug reports have been disabled, either temporarily or permanently
If you still need to submit a bug,
DM @MACHINE_BUILDER#2245 or @SirLich#1658''',
                    colour = discord.Colour.red()
                )
                await channel.send(embed=embed)

            if main_command == BOT_DATA.COMMAND_PREFIXES['bug'] and CONFIG['allow_bug_reports']:
                '''
                allows a user to create a bug report, which gets sent to a channel in another server
                '''

                report_size = (20,1200)

                last_created_bug_report = BUG_REPORTS_BY_USERS.get(author.id, 0.0)

                if last_created_bug_report+CONFIG['bug_report_cooldown'] > time.time():
                    # time delay is in-place
                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Bug report response**
You have submitted a bug report too recently. Please wait a while before attempting to submit another report''',
                        colour = discord.Colour.red()
                    )
                    await channel.send(embed=embed)
                    return

                embed = discord.Embed(
                    title = '',
                    description = f'''\
**Please enter bug report**
Make sure to keep the bug report as descriptive, and as concise as possible
Size constraints of bug report {report_size[0]}-{report_size[1]}
**Do not spam this command or you may be punished**
or type "x" to cancel''',
                    colour = discord.Colour.blue()
                )
                await channel.send(embed=embed)

                try: bug_report_reply = await client.wait_for('message', check=check(author, channel), timeout=300)
                except: bug_report_reply = None

                if bug_report_reply == None:
                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Creation of bug report timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                        colour = discord.Colour.red()
                    )
                    await channel.send(embed=embed)
                    return
                
                bug_report = bug_report_reply.content
                
                if bug_report == 'x':
                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**cancelled creation of bug report**''',
                        colour = discord.Colour.red()
                    )
                    await channel.send(embed=embed)
                    return

                if len(bug_report) < report_size[0] or len(bug_report) > report_size[1]:
                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Bug report response**
Your bug report is not within the size constraints of {report_size[0]}-{report_size[1]}''',
                        colour = discord.Colour.red()
                    )
                    await channel.send(embed=embed)
                    return

                embed_report = discord.Embed(
                    title = 'FAQ Bot Bug Report',
                    description = f'Bug Report Created By **@{author.name}#{author.discriminator}** at **{datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")}**',
                    colour = discord.Colour.blue()
                )

                embed_report.add_field(
                    name = f'Report Content ( From : [{channel.guild.name} - #{channel.name}] )',
                    value = bug_report,
                    inline = False
                )
                
                BUG_REPORTS_BY_USERS[author.id] = time.time()

                embed = discord.Embed(
                    title = '',
                    description = f'''\
**Bug report response**
Your bug report has been submitted''',
                    colour = discord.Colour.green()
                )
                await channel.send(embed=embed)

                bug_report_channel = client.get_channel(BOT_DATA.BUG_REPORT_CHANNEL_ID)
                await bug_report_channel.send(embed=embed_report)






            if main_command == BOT_DATA.COMMAND_PREFIXES['help']:
                # send the help message response
                '''
                The help menu of the bot
                '''
                
                embed = discord.Embed(
                    title = 'Bedrock Scripting FAQ Help',
                    description = 'The Bedrock Scripting FAQ Bot\'s commands are as follows;',
                    colour = discord.Colour.blue()
                )

                embed.add_field(
                    name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.COMMAND_PREFIXES["help"]}',
                    value = 'Displays the bot\'s help menu',
                    inline = False
                )

                embed.add_field(
                    name = f'{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS["list"][0]} [page:int]',
                    value = f'Displays a list of all FAQs, example: "{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS["list"][0]} 1"',
                    inline = False
                )

                embed.add_field(
                    name = f'{BOT_DATA.FAQ_QUERY_PREFIX} [tag]',
                    value = f'Displays the FAQ with the given tag or alias, along with its answer, example: "{BOT_DATA.FAQ_QUERY_PREFIX} some faq"',
                    inline = False
                )

                if CONFIG['allow_bug_reports']:
                    embed.add_field(
                        name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.COMMAND_PREFIXES["bug"]}',
                        value = f'Report a bug within the bot to the developers',
                        inline = False
                    )

                if len(command_split) > 1:

                    if 'fm' in command_split:

                        if BOT_DATA.FAQ_MANAGEMENT_ROLE in [role.name for role in roles]:

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["add"])}',
                                value = 'Create a new FAQ',
                                inline = False
                            )

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["delete"])} [faq tag]',
                                value = 'Delete a FAQ',
                                inline = False
                            )

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["edit"])}',
                                value = 'Edit an existing FAQ',
                                inline = False
                            )

                    if 'admin' in command_split:
                        
                        if BOT_DATA.BOT_ADMIN_ROLE in [role.name for role in roles]:

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["recycle"])}',
                                value = f'Download the {BOT_DATA.FAQ_DATA_FILENAME_BIN} file',
                                inline = False
                            )

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["bug-report-enabled"])} [true/false]',
                                value = f'Enable or disable the bug reporting function',
                                inline = False
                            )

                            embed.add_field(
                                name = f'{BOT_DATA.BOT_COMMAND_PREFIX}{"/".join(BOT_DATA.FAQ_MANAGEMENT_COMMANDS["bug-report-cooldown"])} [int]',
                                value = f'Amount of delay (seconds) between user bug reports',
                                inline = False
                            )

                await channel.send(embed=embed)




                






            '''check if the command is a !fm command'''

            action = main_command

            # print(action)





            if BOT_DATA.BOT_ADMIN_ROLE in [role.name for role in roles]:

                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['bug-report-enabled']:
                    if len(command_split) != 2:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Invalid use of the command**
Make sure to specify true or false in your argument
Example: {BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['bug-report-enabled'][0]} false''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    trueFalse = command_split[1].lower() == 'true'
                    CONFIG['allow_bug_reports'] = trueFalse
                    dumpConfig()

                    if trueFalse:
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Enabled bug reporting**''',
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Disabled bug reporting**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)

                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS["bug-report-cooldown"]:
                    if len(command_split) != 2:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Invalid use of the command**
Make sure to specify the delay in your argument
Example: {BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['bug-report-cooldown'][0]} 300''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    newDelay = int(command_split[1])
                    CONFIG['bug_report_cooldown'] = newDelay
                    dumpConfig()

                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Set bug reporting delay to {newDelay} seconds**''',
                        colour = discord.Colour.green()
                    )
                    await channel.send(embed=embed)



                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['recycle']:
                    # download the recycle bin faq folder
                    await channel.send( f"{BOT_DATA.FAQ_DATA_FILENAME_BIN}", file=discord.File( os.path.join(os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME_BIN) ) )











            if BOT_DATA.FAQ_MANAGEMENT_ROLE in [role.name for role in roles]:
                # print("[DEBUG] caller has adequate privellages to use !fm commands this this command")

                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['add']:
                    # add a FAQ

                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Please enter FAQ tags**
example : tag 1, tag 2, some other tag, or enter "x" to cancel''',
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)

                    try: faq_tags_reply = await client.wait_for('message', check=check(author, channel), timeout=120)
                    except: faq_tags_reply = None

                    if faq_tags_reply == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Creation of new FAQ timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    faq_tags_reply_content = faq_tags_reply.content

                    if faq_tags_reply_content == 'x':
                        # do nothing, since the user cancelled the FAQ creation
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Cancelled FAQ Creation**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    try:

                        aliases = faq_tags_reply_content
                        # !fm add alias1, alias2, something else, comma seperated
                        aliases_list = list( [a.strip().replace(' ','-').lower() for a in aliases.split(',')] )
                        valid_aliases = getValidAliases(aliases_list)

                    except:
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**Invalid use of the command. Make sure to specify FAQ tag(s)**
Error reading FAQ tags, example: 'tag 1, tag 2'""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    if len(valid_aliases) < 1:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Invalid FAQ tags**
Every tag you listed is already in use by other FAQs''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Creating a new FAQ with the tags [{ ', '.join(valid_aliases) }]**
Please enter the FAQ Title, or type "x" to cancel''',
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)

                    try: faq_title_reply = await client.wait_for('message', check=check(author, channel), timeout=120)
                    except: faq_title_reply = None

                    if faq_title_reply == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Creation of new FAQ timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                            colour = discord.Colour.blue()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    faq_title_reply_content = faq_title_reply.content

                    if faq_title_reply_content == 'x':
                        # do nothing, since the user cancelled the FAQ creation
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Cancelled FAQ Creation**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    # faq_title_reply_content is the new FAQ's title

                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Set the FAQ's title to {faq_title_reply_content}**
Please enter the FAQ Description, and include any relative links, or type "x" to cancel''',
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)

                    try: faq_description_reply = await client.wait_for('message', check=check(author, channel), timeout=300)
                    except: faq_description_reply = None

                    if faq_description_reply == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Setting FAQ description timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    faq_description = faq_description_reply.content

                    if faq_description == 'x':
                        # do nothing, since the user cancelled setting the FAQ description
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Cancelled FAQ Creation**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    # faq_description is the new FAQ's description

                    try:
                        new_faq = {
                            "tag": valid_aliases,
                            "title": faq_title_reply_content,
                            "info": faq_description
                        }

                        addFaq(new_faq)

                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Successfully created a new FAQ**''',
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)

                    except:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Error while trying to create new FAQ**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)







                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['edit']:
                    # edit an existing FAQ

                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Please enter tag of FAQ you wish to edit**
enter the FAQ's tag, or enter "x" to cancel''',
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)

                    try: faq_tags_reply = await client.wait_for('message', check=check(author, channel), timeout=120)
                    except: faq_tags_reply = None

                    if faq_tags_reply == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**FAQ edit timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    faq_tag_reply_content = faq_tags_reply.content

                    if faq_tag_reply_content == 'x':
                        # do nothing, since the user cancelled the FAQ editing
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Cancelled FAQ Editing**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    search_for = faq_tag_reply_content

                    if search_for == '':
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**Invalid use of the command. Make sure to specify FAQ tag**
Error reading FAQ tag, example: 'tag 1'""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    


                    found_faq = searchFaqByTag(search_for)

                    if found_faq == None:
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**No FAQ found with tag {search_for}**""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return



                    embed = discord.Embed(
                        title = '',
                        description = f'''\
**Found FAQ ({found_faq['title']})**
Select an attribute of the FAQ to edit,
valid attributes:
_ - t: title_
_ - ta: tags_
_ - d: description_
or type "x" to cancel''',
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)


                    try: faq_edit_attribute = await client.wait_for('message', check=check(author, channel), timeout=120)
                    except: faq_edit_attribute = None

                    if faq_edit_attribute == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    faq_edit_attribute_choice = faq_edit_attribute.content

                    if faq_edit_attribute_choice == 'x':
                        # do nothing, since the user cancelled the FAQ creation
                        embed = discord.Embed(
                            title = '',
                            description = f'''**Cancelled FAQ Editing**''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return



                    if faq_edit_attribute_choice in ['t', 'title']:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Please enter a new title for the FAQ, or enter "x" to cancel''',
                            colour = discord.Colour.blue()
                        )
                        await channel.send(embed=embed)
                        try:
                            msgresp = await client.wait_for('message', check=check(author, channel), timeout=120)
                            response = msgresp.content
                        except:
                            embed = discord.Embed(
                                title = '',
                                description = f'''\
**FAQ edit timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return
                        
                        deleteFaq( found_faq['tag'][0] )
                        found_faq['title'] = response
                        addFaq(found_faq)

                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Edited FAQ title''',
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)





                    elif faq_edit_attribute_choice in ['ta', 'tags']:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Please enter the new tags for the FAQ, or enter "x" to cancel''',
                            colour = discord.Colour.blue()
                        )
                        await channel.send(embed=embed)
                        try:
                            msgresp = await client.wait_for('message', check=check(author, channel), timeout=120)
                            response = msgresp.content
                        except:
                            embed = discord.Embed(
                                title = '',
                                description = f'''\
**Editing FAQ timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return

                        tags = list( [t.strip().replace(' ','-').lower() for t in response.split(',')] )

                        if tags == []:
                            embed = discord.Embed(
                                title = '',
                                description = f'''\
**Invalid FAQ tags**
You must enter one or more tags, example: "tag 1, tag 2"''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return
                        
                        deleteFaq( found_faq['tag'][0] )

                        valid_tags = getValidAliases(tags)

                        if len(valid_tags) == 0:
                            embed = discord.Embed(
                                title = '',
                                description = f'''\
**Invalid FAQ tags**
All the tags you entered are already used in other FAQs, please use different tags''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return

                        found_faq['tag'] = valid_tags
                        addFaq(found_faq)

                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Edited FAQ tags''',
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)




                    elif faq_edit_attribute_choice in ['d', 'description']:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Please enter a new description for the FAQ, or enter "x" to cancel''',
                            colour = discord.Colour.blue()
                        )
                        await channel.send(embed=embed)
                        try:
                            msgresp = await client.wait_for('message', check=check(author, channel), timeout=120)
                            response = msgresp.content
                        except:
                            embed = discord.Embed(
                                title = '',
                                description = f'''\
**Editing FAQ timed out**
If you would like to retry, please re-type the command "{message.content}"''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return
                        
                        if response == '':
                            embed = discord.Embed(
                                title = '',
                                description =f'''\
**Invalid FAQ description**
You cannot leave the description of a FAQ blank''',
                                colour = discord.Colour.red()
                            )
                            await channel.send(embed=embed)
                            return
                        
                        deleteFaq( found_faq['tag'][0] )
                        found_faq['info'] = response
                        addFaq(found_faq)

                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Editing FAQ**
Edited FAQ description''',
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)


                    




                    

                if action in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['delete']:
                    # delete a faq with a certain tag

                    try:
                        faq_tag = ' '.join( command_split[1:len(command_split)] ).strip().replace(' ','-').lower()
                        assert faq_tag != ''
                    except:
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**Invalid use of the command. Make sure to specify a FAQ tag**
Example use : '{BOT_DATA.BOT_COMMAND_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['delete'][0]} faq tag'""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    if findFaqByTag(faq_tag) == None:
                        embed = discord.Embed(
                            title = '',
                            description = f'''\
**Invalid FAQ tag**
There is no FAQ with the tag "{faq_tag}", use '{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['list'][0]}' to list out FAQs''',
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return

                    embed = discord.Embed(
                        title = '',
                        description = f"""\
**Found FAQ**
Are you sure you wish to delete this FAQ? Deleting a FAQ is permenant
To confirm, the FAQ you are about to delete is titled **{findFaqByTag(faq_tag)['title']}**
Type yes to continue, or anything else to cancel""",
                        colour = discord.Colour.blue()
                    )
                    await channel.send(embed=embed)

                    try: faq_delete_reply = await client.wait_for('message', check=check(author, channel), timeout=25)
                    except: faq_delete_reply = None

                    if faq_delete_reply == None:
                        # do nothing, since the user cancelled deleting the FAQ
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**FAQ deletion timed out**
FAQ delete confirmation message timed out
If you would like to retry, please re-type the command \"{message.content}\"""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)
                        return
                    
                    if faq_delete_reply.content == 'yes':
                        # delete the FAQ
                        deleteFaq(faq_tag)
                        embed = discord.Embed(
                            title = '',
                            description = f"""**FAQ has been deleted**""",
                            colour = discord.Colour.green()
                        )
                        await channel.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title = '',
                            description = f"""\
**FAQ deletion cancelled**
The FAQ '{faq_tag}' has not been deleted""",
                            colour = discord.Colour.red()
                        )
                        await channel.send(embed=embed)












    if message.content.startswith(BOT_DATA.FAQ_QUERY_PREFIX):
        # check that this message is a command, e.g: '!help'

        print(f"[DEBUG] command (FAQ) called : {message.content}")
        

        
        command_request = message.content.split( BOT_DATA.FAQ_QUERY_PREFIX, 1 )[-1]
        command_split = command_request.split(' ')
        main_command = command_split[0]
    
        if main_command in BOT_DATA.FAQ_MANAGEMENT_COMMANDS['list']:
            # list out all the FAQ tags and text

            list_page = 1
            if len(command_split) > 1:
                try: list_page = int(command_split[1])
                except: list_page = 1
            list_page -= 1

            embed = discord.Embed(
                title = 'All FAQs',
                description = '---',
                colour = discord.Colour.blue()
            )

            all_faq_entries = faq_data['faq_data']
            paginated_faq_entries = paginate_list(all_faq_entries, BOT_DATA.PAGINATE_FAQ_LIST)

            if list_page > len(paginated_faq_entries)-1:
                list_page = 0
            
            if len(paginated_faq_entries) < 1:
                embed.add_field(
                    name = 'ERROR: No FAQs Found',
                    value = '-',
                    inline = False
                )
            
            else:
                for faq_entry in paginated_faq_entries[ list_page ]:
                    embed.add_field(
                        name = faq_entry['title'].title(),
                        value = ', '.join( faq_entry['tag'] ),
                        inline = False
                    )
            
            embed.set_footer(text=f'''\
page {list_page+1} of {len(paginated_faq_entries)}
({len(all_faq_entries)} total faq entries)
Use "{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['list'][0]} [page]" to list a given page of FAQs''')

            await channel.send(embed=embed)

            return



        try:
            faq_tag_searches = message.content.split( BOT_DATA.FAQ_QUERY_PREFIX, 1 )[-1].strip().replace(' ','-').lower()
        except:
            faq_tag_searches = None

        if not faq_tag_searches:
            faq_tag_searches = None
    
        if faq_tag_searches == None:
#             embed = discord.Embed(
#                 title = '',
#                 description = f"""\
# **Invalid use of the command. Make sure to specify FAQ tag(s)**
# Example use :'{BOT_DATA.FAQ_QUERY_PREFIX} some faq tag'
# You can also use '{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['list'][0]}' to see a list of all FAQs""",
#                 colour = discord.Colour.red()
#             )
#             await channel.send(embed=embed)
            return



        if len(list([c for c in faq_tag_searches if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'])) == 0:
            return


        faq = searchFaqByTag( faq_tag_searches )

        if faq == None:
            embed = discord.Embed(
                title = '',
                description = f"""\
**No FAQs could be found when searching for "{faq_tag_searches}"**
You can use '{BOT_DATA.FAQ_QUERY_PREFIX}{BOT_DATA.FAQ_MANAGEMENT_COMMANDS['list'][0]}' to see a list of all FAQs""",
                colour = discord.Colour.red()
            )
            await channel.send(embed=embed)
            return

        embed = discord.Embed(
            title = f'{faq["title"]}',
            description = faq["info"],
            colour = discord.Colour.blue()
        )

        await channel.send(embed=embed)










if not os.path.exists( os.path.join( os.getcwd(), BOT_DATA.FAQ_DATA_FILENAME ) ):
    print("[DEBUG] making empty faq file, since faq file is missing")
    dumpFaqFile(
        {
            "faq_data": [ ]
        }
    )



faq_data = loadFaqFile()

print("[DEBUG] loaded faq data")
# print(json.dumps(faq_data,indent=2))

client.run( open( os.path.join(os.getcwd(), BOT_DATA.TOKEN_FILENAME) , 'r').readline().strip() )