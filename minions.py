import globals
import game
import random
from character import Character


class Minion(Character):
    def __init__(self):
        super().__init__()
        self.trueAlignment = 'evil'
        self.trueType = 'minion'


class Poisoner(Minion):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'poisoner'
        self.turnOrder = 1
        super().match_visible_to_true()

    async def night_ability(self):
        self.wakeTonight = True
        prompt = 'Choose player to poison\n**~choose player**'

        iMessage = await super().wait_on_self(prompt, ['choose'])
        target = iMessage.payload

        message = 'Target confirmed: ' + target.nickname
        await self.send_to_self(message)

        if self.poisoned:
            return

        target.poison(self.trueCharacter)
        self.lastTarget = target

    def reset_night_ability(self):
        if self.lastTarget is not None:
            self.lastTarget.unpoison(self.trueCharacter)
        self.lastTarget = None


class ScarletWoman(Minion):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'scarlet woman'
        self.turnOrder = 30
        super().match_visible_to_true()


class Spy(Minion):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'spy'
        self.visibleAlignment = 'good'
        self.visibleAlignmentStorage = self.visibleAlignment
        # can put this stuff in secondary_init?
        options = ['chef', 'empath', 'fortune teller', 'investigator', 'librarian', 'mayor', 'monk', 'ravenkeeper',
                   'slayer', 'soldier', 'undertaker', 'virgin', 'washerwoman']
        choice = random.randint(0, len(options) - 1)
        self.visibleType = 'townsfolk'
        self.visibleTypeStorage = self.visibleType
        self.visibleCharacter = options[choice]
        self.visibleCharacterStorage = self.visibleCharacter
        self.turnOrder = 90

    async def night_ability(self):
        self.wakeTonight = True
        if not self.poisoned:
            await super().send_to_self(globals.logger.grimoire)
        globals.logger.reset_grimoire()

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
