import globals
import game
from character import Character
from interpreter import interpret_general, wait_for_message
import databases


class Demon(Character):
    def __init__(self):
        super().__init__()
        self.trueAlignment = 'evil'
        self.trueType = 'demon'

    # make sure to handle poisoned
    async def night_ability(self):
        prompt = 'Choose player to kill\n**~choose player**'

        iMessage = await super().wait_on_self(prompt, ['choose'])

        message = 'Target confirmed: **' + iMessage.payload.nickname + '**'

        await self.send_to_self(message)

        if iMessage.payload.alias == 'ben' and game.numDays == 1:
            await self.send_to_self('Haha get fucked Ben')

        return iMessage.payload

    async def die(self, source):
        if await super().die(source):
            scarletWoman = game.random_of_property(lambda p: p.trueCharacter == 'scarlet woman')
            if scarletWoman is not None and not scarletWoman.poisoned:
                self.transfer_demon(scarletWoman)
            return True
        else:
            return False

    def transfer_demon(self, target):  # target is the person being given self's character
        # populate with self's character info, target's personal info
        new = databases.characterDatabase[self.trueCharacter]

        new.clientUser = target.clientUser
        new.nickname = target.nickname
        new.alias = target.alias
        new.dmChannel = target.dmChannel

        new.position = target.position
        new.leftNeighbor = target.leftNeighbor
        new.rightNeighbor = target.rightNeighbor

        new.canNominate = target.canNominate
        new.canBeNominated = target.canBeNominated
        new.wantVote = target.wantVote
        new.wantSleep = target.wantSleep

        # new.lastTarget = self.lastTarget  # not needed, old demon will still reset_night_ability

        if game.nominatedPlayer == target:
            game.nominatedPlayer = new
        if game.playerOnDeathRow == target:
            game.playerOnDeathRow = new

        game.players[target.position] = new
        if target in game.nightList:
            game.nightList.remove(target)


    # def transfer_demon(self, target):
    #     # make sure to copy over all fields and functions
    #     target.trueType = 'demon'
    #     target.trueCharacter = 'imp'
    #     target.match_visible_to_true()
    #     target.turnOrder = self.turnOrder
    #
    #     target.night_ability = self.night_ability
    #     target.die = self.die


class Imp(Demon):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'imp'
        self.turnOrder = 40
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays != 0:
            self.wakeTonight = True
            self.lastTarget = await super().night_ability()

            if self.poisoned:
                return

            if self.lastTarget == self:
                newImp = game.random_of_property(lambda p: p.alive and p.trueType == 'minion' and p.trueCharacter != 'scarlet woman')
                if newImp is None:
                    newImp = game.random_of_property(lambda p: p.alive and p.trueType == 'minion')
                if newImp is not None:
                    self.transfer_demon(newImp)

            await self.lastTarget.die('demon')
