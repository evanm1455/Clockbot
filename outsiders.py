import globals
import game
import random
import databases
from character import Character


class Outsider(Character):
    def __init__(self):
        super().__init__()
        self.trueAlignment = 'good'
        self.trueType = 'outsider'


# Trouble Brewing
class Drunk(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'drunk'
        super().match_visible_to_true()

    def secondary_init(self):
        possible = game.possibleStartingRoles[0]
        possible = list(set(possible) - set(game.rolesInPlay))
        choice = random.choice(possible)
        other = databases.characterDatabase[choice]

        # set up data for other
        other.position = self.position
        other.clientUser = self.clientUser
        other.nickname = self.nickname
        other.alias = self.alias
        other.dmChannel = self.dmChannel
        other.poisoned = True

        # set up data for self
        self.imitating = other.trueCharacter
        self.turnOrder = other.turnOrder

        # assign other functions to self
        self.nominated = other.nominated
        self.slayer_ability = other.slayer_ability
        self.night_ability = other.night_ability
        self.reset_night_ability = other.reset_night_ability
        self.die = other.die

        self.poisoned = True

    def poison(self, source):
        return

    def unpoison(self, source):
        return


class Recluse(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'recluse'
        self.visibleAlignment = 'evil'
        self.visibleAlignmentStorage = self.visibleAlignment
        options = ['poisoner', 'scarlet woman', 'imp']  # can make this not be hard coded with secondary_init?
        choice = random.randint(0, len(options) - 1)
        if choice < 2:
            self.visibleType = 'minion'
        else:
            self.visibleType = 'demon'
        self.visibleTypeStorage = self.visibleType
        self.visibleCharacter = options[choice]
        self.visibleCharacterStorage = self.visibleCharacter

    def poison(self, source):
        super().poison(source)

        if not self.alive:
            return

        self.match_visible_to_true()

    def unpoison(self, source):
        super().unpoison(source)

        if not self.alive:
            return

        if not self.poisoned:
            self.visibleAlignment = self.visibleAlignmentStorage
            self.visibleType = self.visibleTypeStorage
            self.visibleCharacter = self.visibleCharacterStorage

    async def die(self, source):
        if not self.alive:
            return False

        if await super().die(source):
            self.match_visible_to_true()
            return True
        else:
            return False


class Saint(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'saint'
        super().match_visible_to_true()

    async def die(self, source):
        if not self.alive:
            return False

        dying = await super().die(source)
        if dying and source == 'execution' and not self.poisoned:
            await globals.mainChannel.send('**' + self.nickname + '** has been executed.\nNice job guys y\'all killed the saint')
            await game.game_end('evil')
        else:
            return dying


# Bad Moon Rising
class Goon(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'goon'
        super().match_visible_to_true()

    async def die(self, source):
        pass


class Gypsy(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'gypsy'
        super().match_visible_to_true()

    async def die(self, source):
        pass


class Lunatic(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'lunatic'
        super().match_visible_to_true()


class Tinker(Outsider):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'tinker'
        super().match_visible_to_true()

    async def night_ability(self):
        if self.poisoned:
            return

        if random.randint(0, 3) == 0:
            await self.die('tinker')

    async def die(self, source):
        if not self.alive:
            return False

        if source == 'tinker':
            self.alive = False
            return True

        if not await super().die(source):
            if bool(random.getrandbits(1)):
                self.alive = False
                return True
        self.alive = False
        return True
