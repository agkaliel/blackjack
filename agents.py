import blackjack
from tabulate import tabulate
import copy
import re


def probBust(hand, target):
    maximum = target-hand

    #if target == hand, i.e. we are already at 21, then ProbBust = 1
    if maximum == 0:
        return 1
    #if target - hand >= 10 i.e. we are at 11 or lower, there is no possible way to bust.  
    if maximum >= 10:
        return 0
    #if the maximum is between 1 and 9, the probability of busting is the number of possible values greater than maximum (13 - maximum) out of thirteen
    return (13-maximum)/13


#Assumptions:
#Game is played with 8 decks
#Assume we start with a fresh 8 decks after each hand


def agentTest(agent):
    frequencies = []
    probabilities = []
    #Populate frequences with 12 0's, as there are 12 values to keep track of between 11 and 2s
    for i in range(12):
        frequencies.append(0)
        probabilities.append(0)
    sampleSize = 100

    #Play blackjack through "sampleSize" games
    for i in range(sampleSize):
        game = blackjack.BlackJack(8)
        game.start_game()
        while game.state.terminate == 0:
            action = game.act(agent)
        final = blackjack.BlackJack.calc(game.state.player_hand)
        if final >= 22:
            frequencies[11] += 1
        else:
            frequencies[final - 11] += 1

    for i in range(12):
        probabilities[i] = frequencies[i]/sampleSize

    return probabilities


#The function dealer test is basically a modified version of agentTest()
#The list startValues contains a list of lists, where the first element 
#refers to the dealer starting with an ace, the second element to the dealer
#starting with a 2 ect.  There are 10 lists in start value.  Each list in start
#values contains the frequencies with which the dealer ended on each final hand
#value.  So in the end, we get a 10*12 grid.  We convert these frequencies to
#probabilties at the end.
def dealerTest(agent):
    startValues = []
    for i in range(10):
        startValues.append([])


    #Populate each the 10 lists in startValues with 12 0's, as there are 12 "finish" values to keep track of between 11 and 22
    for startValue in startValues:
        for i in range(12):
            startValue.append(0)
    sampleSize = 100


    #Play blackjack through "sampleSize" games
    for i in range(sampleSize):
        game = blackjack.BlackJack(8)
        game.start_game()

        while game.state.terminate == 0:
            first = game.state.player_hand[0][0]
            if game.state.player_hand[0][1] == '0':
                first = first + '0'
            if first == 'A':
                first = 1
            elif first == 'J' or first == 'Q' or first == 'K':
                first = 10
            else:
                first = int(float(first))

            action = game.act(agent)

        final = blackjack.BlackJack.calc(game.state.player_hand)
        if final >= 22:
            startValues[first-1][11] += 1
        else:
            startValues[first-1][final - 11] += 1

    probabilities = copy.deepcopy(startValues)
    for row in range(10):
        for col in range(12):
            probabilities[row][col] = (startValues[row][col] / sum(startValues[row]))
    print(tabulate(startValues))
    text_file = open("outputbetter.txt", "w")
    text_file2 = open("outputbetterraw.txt", "w")
    text_file.write(tabulate(probabilities))
    text_file.write(tabulate(startValues))
    text_file2.write(str(probabilities))
    text_file.close()
    text_file2.close()
    print(tabulate(probabilities))



def prepSophAgent():
    dealerTestOutput = open('output.txt', 'r')
    dealerProbs = []
    #Get the data from the output file from the dealerTest() function
    for line in dealerTestOutput:
        inner_list = [elt.strip() for elt in line.split('  ')]
        dealerProbs.append(inner_list)

    agentProbs = []

    #want win/tie probabilities for hit/stand for 12 through 21 (10 values)
    #each row will refer to the dealers start card, each column to the players hand value
    for row in range(10):
        agentProbs.append([])
        for col in range(10):
            #The first element of each tuple (actually a list so I can change assignments) corresponds to the
            #probability of a win/tie if the player hits,
            #and the second element of each tuple corresponds to the probability of a win/tie if the player stands,
            #corresponding to the dealer card and player card at that location.
            agentProbs[row].append([0,0])

    #If we are at 21, we always want to stay
    for rowNum, row in enumerate(agentProbs):
        row[9][1] = 1
        #filling in the "stay" probabilities
        for i in reversed(range(0,9)):
            #probWinStay is the probability that the value we currently have is good enough to win or tie
            #i.e. the probability that we will win or tie with a stay
            probWinStay = 0
            #0 in the dealerProbs list corresponds to the dealer finishing with 17
            #0 in the agentProbs list corresponds to the action with a hand value of 12
            #we want to include ties, so this means an offset of 4
            for dealerFinish in range(i-4):
                probWinStay += float(dealerProbs[rowNum][dealerFinish])
            #add the probability of the dealer busting
            probWinStay += float(dealerProbs[rowNum][5])
            row[i][1] = round(probWinStay,5)
        #filling in the "hit" probabilities
        for i in reversed(range(0,9)):
            probWinHit = 0
            for nextPossible in range(i+1,10):
                probWinHit += max(row[nextPossible])/13
            row[i][0]=round(probWinHit,5)

    #Now we make a table for the actual decisions we will make
    strategy = []
    for row in range(10):
        strategy.append([])
        for col in range(10):
            strategy[row].append([])
            if agentProbs[row][col][0] > agentProbs[row][col][1]:
                strategy[row][col] = 'H'
            else:
                strategy[row][col] = 'S'




    output = open('probabilityTable.txt', 'w')
    output.write(tabulate(agentProbs))
    output2 = open('agentStrategy.txt', 'w')
    output2.write(tabulate(strategy))




       


class ThoughtlessAgent:
    def __init__(self, actions=('H', 'S', 'D')):
        self.actions = actions
    
    def act(self, state):
        return self.actions[0]
    
class BasicAgent:
    def act(self, state):
        if blackjack.BlackJack.calc(state.player_hand) > 16:
            return 'S'
        else:
            return 'H'

class SophAgent:
    strategyFile = open('agentStrategy.txt', 'r')
    strategy = []
    #Get the data from the output file from the dealerTest() function
    for line in strategyFile:
        inner_list = [elt.strip() for elt in line.split('  ')]
        strategy.append(inner_list)
    strategy = strategy[1:-1]

    def act(self, state):
        dealer = blackjack.BlackJack.calc(state.dealer_hand)
        player = blackjack.BlackJack.calc(state.player_hand)
        if dealer == 11:
            dealer = 1
        if player >= 12 and player <= 21:
            move = self.strategy[dealer - 1][player - 12]
            return move
        else:
            return 'H'


class RationalAgent:
    cardsPlayed = []
    def act(self,state):

        num_decks = state.num_decks
        print(state.player_hand)
        print(state.dealer_hand)
        print()
        if blackjack.BlackJack.calc(state.player_hand) > 16:
            return 'S'
        else:
            return 'H'





class CommandLineAgent:
    interactive = True
    
    def act(self, state):
        """
        Display the game state information and prompt for action choice
        """
        if state.terminate == 0:
            return input("Choose an action [H]it, [S]tand, [D]ouble:").upper()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    agent = BasicAgent()
    print(prepSophAgent())
