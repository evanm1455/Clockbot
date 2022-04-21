import globals
from interpreter import wait_for_message
import game

# turn order classes
# 0 evil poison (non demon)
# 1 good drunk
# 2 good disruptive (non drunk)
# 3 evil pre-demon
# 4 demon
# 5 evil killing (non demon)
# 6 outsiders
# 7 good resurrection
# 8 good information
# 9 evil information
# 10 no night ability


class Character:
    def __init__(self):
        # player data
        self.clientUser = None
        self.nickname = None  # i think it would be good to always have the nickname be in bold
        self.alias = None  # same for alias
        self.dmChannel = None

        # positional data
        self.position = None
        self.leftNeighbor = None
        self.rightNeighbor = None

        # character data
        self.visibleAlignment = None
        self.trueAlignment = None
        self.visibleType = None
        self.trueType = None
        self.visibleCharacter = None
        self.trueCharacter = None
        self.imitating = None
        self.turnOrder = 100
        self.usedAbility = False
        self.lastTarget = None
        self.wakeTonight = False
        self.causeOfDeath = None

        # status effects
        self.alive = True
        self.poisoned = False
        self.poisonedSource = None
        self.monkProtected = False
        self.innkeeperProtected = False

        # democracy
        self.canNominate = True
        self.canBeNominated = True
        self.canVote = True
        self.wantVote = False
        self.wantSleep = False

    def secondary_init(self):
        pass

    # send a message to self
    async def send_to_self(self, message):
        await self.dmChannel.send(message)

    # send prompt to channel and wait for a reply on the same channel
    async def wait_on_self(self, prompt, commands, invalids=None):
        return await wait_for_message(self.dmChannel, prompt, self.clientUser, commands, invalids)

    async def die(self, source):  # needs to be async b/c we sometimes overwrite it with an async fxn?
        if not self.alive:
            return False

        # survivals
        if source == 'demon' and self.monkProtected:  # monk
            return False

        if self.innkeeperProtected:  # innkeeper
            return False

        if self.trueAlignment == 'good':  # tea lady
            teaLady = game.all_of_property(lambda p: p.trueCharacter == 'tea lady')
            if teaLady is not None:
                if self.alive_neighbor('left') or self.alive_neighbor('right') == teaLady:  # check adjacent
                    if (not teaLady.poisoned and
                            teaLady.alive_neighbor('left').trueAlignment == 'good' and
                            teaLady.alive_neighbor('right').trueAlignment == 'good'):  # check tea lady proc
                        return False

        # death
        self.causeOfDeath = source
        self.alive = False
        return True

    def match_visible_to_true(self):
        self.visibleAlignment = self.trueAlignment
        self.visibleType = self.trueType
        self.visibleCharacter = self.trueCharacter

    def dawn_reset(self):
        self.innkeeperProtected = False
        self.monkProtected = False

    def dusk_reset(self):
        self.canNominate = True
        self.canBeNominated = True
        self.wantVote = False
        self.wantSleep = False
        if self.poisonedSource in ['innkeeper', 'minstrel', 'sailor']:
            self.poisoned = False
            self.poisonedSource = None

    def alive_neighbor(self, direction):
        if direction == 'left':
            current = self.leftNeighbor
            while not current.alive:
                current = current.leftNeighbor
        elif direction == 'right':
            current = self.rightNeighbor
            while not current.alive:
                current = current.rightNeighbor
        return current

    # belongs to all characters so that they can bluff slayer
    async def slayer_ability(self, target):
        message = '**' + self.nickname + '** slays **' + target.nickname + '**! It isn\'t very effective'
        if target.alias == 'will':
            globals.timesWillSlain += 1
            message += '\nWill Nute now has ' + globals.timesWillSlain + ' crossbow bolts protruding from his chest'
        await globals.mainChannel.send(message)

    # stub function. will be overwritten
    async def night_ability(self):
        pass

    def reset_night_ability(self):
        self.wakeTonight = False

    def unpoison(self, source):  # repeatedly unpoison then repoison for poisons lasting >1 day
        if not self.poisoned:
            return
        self.poisoned = not source == self.poisonedSource
        self.poisonedSource = None

    def poison(self, source):
        self.poisoned = True
        self.poisonedSource = source

    async def nominated(self, source):
        pass

    def __str__(self):
        return self.nickname + ': ' + self.trueCharacter

    def __lt__(self, other):
        return self.turnOrder < other.turnOrder

    def __le__(self, other):
        return self.turnOrder <= other.turnOrder

    def __gt__(self, other):
        return self.turnOrder > other.turnOrder

    def __ge__(self, other):
        return self.turnOrder >= other.turnOrder

    def __eq__(self, other):
        return self.alias == other.alias

    def __ne__(self, other):
        return self.alias != other.alias
