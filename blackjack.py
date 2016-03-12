"""Blackjack dealer and experiment runner.

Usage: 
    blackjack.py [-vd] [--hands=N] [--decks=M][--seed=S][--agent=AGENT]


Options:
    -h --help
    -v              Verbose mode, show action output messages.
    -d              Debug mode, execute docstring tests.
    --hands=N       Number of hands to play [default: 100]
    --decks=M       Number of decks to shuffle (reshuffles once half the cards have been played) [default: 8]
    --agent=AGENT   Name of python agent class [default: BasicAgent]
    --seed=S        Number to seed the random generator with.
"""

import random
import agents
from docopt import docopt
from datetime import datetime
import time

class GameState:
    def __init__(self, num_decks=2):
        self.dealer_hand = []
        self.player_hand = []
        self.win_total = 0
        self.terminate = 0
        self.num_decks = num_decks  

    def reset(self):
        self.dealer_hand = []
        self.player_hand = []
        self.win_total = 0
        self.terminate = 0

SUITS = ['S', 'C', 'H', 'D']
FACE_CARDS = ['J', 'Q', 'K']
FACES = ['A']+[str(i) for i in range(2, 11)]+FACE_CARDS
STD_DECK = ["{}{}".format(f, s) for s in SUITS for f in FACES]

class Deck:
    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.halfway = num_decks * 26
        self.reset()

    def reset(self):
        self.deck = [c for c in STD_DECK*self.num_decks]

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self, num_cards=1, num_players=1):
        """
        Deal out the specified number of cards to the specified number of players.
        Returns a tuple of tuples and modifies the deck.

        >>> d = Deck()
        >>> d.deal()
        [['KD']]
        >>> d.deal(2)
        [['QD', 'JD']]
        >>> d.deal(num_players=3)
        [['10D'], ['9D'], ['8D']]
        >>> d.deal(num_players=3, num_cards=2)
        [['7D', '6D'], ['5D', '4D'], ['3D', '2D']]
        """
        if len(self.deck) < self.halfway:
            self.reset()
            self.shuffle()
        return [[self.deck.pop() for _ in range(num_cards)] for _ in range(num_players)]

class BlackJack:
    actions = ('H', 'S', 'D')

    @classmethod    
    def calc(self, hand):
        """
        calculate the value of the given hand
        >>> BlackJack.calc(['AS', '10D'])
        21
        >>> BlackJack.calc(['AS', '10D', '3H'])
        14
        >>> BlackJack.calc(['AS', '7D', '3H'])
        21
        >>> BlackJack.calc(['AS', '6D', '3H'])
        20
        >>> BlackJack.calc(['2S', '3D'])
        5
        >>> BlackJack.calc(['8C', '7H', '9D'])
        24
        """
        total = 0
        num_aces = 0
        for c in hand:
            if c[0] == 'A':
                num_aces += 1
            elif c[0] in FACE_CARDS or c[0] == '1':
                total += 10
            else:
                total += int(c[0])
        # if total is greater than 10 the aces must count as 1s
        if total > 10 or num_aces == 0:
            return total + num_aces
        else:
            return total + 11 + (num_aces-1)    


    def __init__(self, num_decks=2):
        """
        Set up the decks and shuffle the cards
        """
        self.state = GameState(num_decks)
        self.dealer_card = ''
        self.deck = Deck(num_decks=self.state.num_decks)

    def display_hand(self, name="Player", cards=None):
        if cards == None:
            if name=="Player":
                cards = self.state.player_hand
            else:
                cards = self.state.dealer_hand

        print("{} has {} for total of {}.".format(name, 
                                                  tuple(cards), 
                                                  self.calc(cards)))

    def start_game(self):
        # deal cards
        self.state.reset()
        self.deck.shuffle()
        (self.state.dealer_hand, self.state.player_hand) = self.deck.deal(num_cards=2, num_players=2)
        # hide one dealer card
        self.dealer_card = self.state.dealer_hand.pop()
        self.state.win_total = 1        

    def act(self, agent):
        """
        Request an action from an agent object, update game state accordingly
        """
        choice = agent.act(self.state)
        if choice == 'H' or choice == 'D':
            self.state.player_hand.extend(self.deck.deal()[0])
            if choice == 'D':
                self.state.win_total *= 2
        if choice == 'S' or choice == 'D':
            self.state.terminate = 1
        elif choice != 'H':
            print("Sorry, invalid action {}.".format(choice))

        if self.calc(self.state.player_hand) > 21:
            self.state.terminate = -1
        return choice


    def final(self, agent=None):
        self.state.dealer_hand.append(self.dealer_card)
        p = self.calc(self.state.player_hand)

        # check if the player lost already
        if p > 21:
            self.state.terminate = -1
            if agent:
                agent.act(self.state)
            return self.state.terminate * self.state.win_total

        # otherwise play out the dealer
        while self.calc(self.state.dealer_hand) < 17:
            self.state.dealer_hand.extend(self.deck.deal()[0])
        self.state.terminate = 1

        d = self.calc(self.state.dealer_hand)

        # see how the dealer and player compare
        if d > 21 or p > d:
            self.state.terminate = 1
        elif p==d:
            self.state.win_total = 0
        else:
            self.state.terminate = -1
        # let the player know what the final card state was
        if agent:
            agent.act(self.state)
        return self.state.win_total * self.state.terminate

def playAgain():
    choice = input("Play again? y/n:")
    if choice and choice[0].lower() == 'y':
        print("Hooray!")
        return True
    else:
        print("TTYL")
        return False

def main(num_hands=10, num_decks=8, verbose=True, agent_class="CommandLineAgent", seed=None):
    # double-check verbosity, if we're playing on the command line we should probably tell the player what's going on
    if agent_class=="CommandLineAgent":
        verbose = True

    # proper randomization
    try:
        seed = int(seed)
    except TypeError:
        seed = int(time.mktime(datetime.now().timetuple()))

    if verbose:
        print("Starting with seed {}".format(seed))
    random.seed(seed)
    try:
        num_decks = int(num_decks)
    except:
        num_decks = 8
    try:
        num_hands = int(num_hands)
    except:
        num_hands = 10

    game = BlackJack(num_decks)
    agent = getattr(agents, agent_class)()
    total = 0
    num_wins = 0
    num_losses = 0
    for hand in range(num_hands):
        game.start_game()
        if verbose:
            game.display_hand()
            game.display_hand("Dealer")

        while game.state.terminate == 0:
            action = game.act(agent)
            if verbose:
                print("Player chose {}".format(action))
                game.display_hand()

        p = game.calc(game.state.player_hand)
        if verbose:
            if p > 21:
                print("Player went bust.")                
            else:
                print("Player stays at {}".format(game.calc(game.state.player_hand)))
        result = game.final(agent)
        if verbose:
            game.display_hand("Dealer")

        if result > 0:
            if verbose:
                print("--WIN--")
            num_wins += 1
        elif result < 0:
            if verbose:
                print("--lose--")
            num_losses += 1
        elif verbose:
            print("--Tie--")
        total += result
        if hasattr(agent, 'interactive'):
            if not playAgain():
                break
        if verbose:
            print("Done game {} at {}.".format(hand, result))
    num_ties = hand + 1 - num_wins - num_losses
    print("Total winnings: {} over {} games.\n with {} wins, {} losses, {} ties.".format(total, 
                                                                                         hand + 1,
                                                                                         num_wins,
                                                                                         num_losses,
                                                                                         num_ties))


if __name__ == '__main__':
    options = docopt(__doc__)
    if (options['-d']):
        import doctest
        doctest.testmod()
    main(verbose=options['-v'], 
         num_hands=options['--hands'], 
         agent_class=options['--agent'], 
         num_decks=options['--decks'],
         seed=options['--seed'])