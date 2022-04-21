import datetime
import game
import databases
import globals
import discord

dividerOne = '--<>--<>--<>--<>--<>--<>--<>--'
dividerTwo = '--<>--<>--<>--<>--<>--<>--<>--<>--<>--<>--<>--<>--<>--<>--'


class Logger:
    def __init__(self):
        time = 'logs/' + str(datetime.datetime.now())[:16]
        time = time.replace(':', '.') + '.txt'
        self.name = time
        self.file = open(time, 'w')
        self.grimoire = ''

    def log(self, phase, message):
        source = databases.aliasDatabase[message.author.id]
        try:
            dest = databases.aliasDatabase[message.channel.recipient.id]
        except AttributeError:
            dest = message.channel.name
        line = '[' + phase + '][' + source + '->' + dest + '] ' + message.content
        print(line)
        self.file.write(line + '\n')
        self.add_to_grimoire(line + '\n')

    async def upload_log(self):
        await globals.mainChannel.send(file=discord.File(self.name))

    def add_to_grimoire(self, text):
        self.grimoire += text

    def reset_grimoire(self):
        self.grimoire = game.print_roles()

    def phase_change_minor(self, text):
        diff = len(dividerOne) - len(text)
        filler = '-' * int(diff / 2)
        line = '\n' + dividerOne + '\n' + filler + text + filler + ('-' if diff % 2 != 0 else '') + '\n' + dividerOne + '\n\n'
        self.file.write(line)

    def phase_change_major(self, text):
        diff = len(dividerTwo) - len(text)
        filler = '-' * int(diff/2)
        line = '\n' + dividerTwo + '\n' + filler + text + filler + ('-' if diff % 2 != 0 else '') + '\n' + dividerTwo + '\n\n'
        self.file.write(line)

    def save(self):
        self.file.close()
        self.file = open(self.name, 'a')

    async def shutdown(self):
        print('Shutting down logger')
        self.file.close()
        self.file = None
        await self.upload_log()
