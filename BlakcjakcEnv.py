import gym 
from gym import spaces
from enum import Enum
import numpy as np

class Actions(Enum):
    HIT = 0
    STAND = 1
    SPLIT = 2
    DOUBLE = 3
    
class BlackjackEnv(gym.Env):
    #Changer reward method to return the gain of the agent
    
    def __init__(self, number_deck):
        super().__init__()
        self.number_deck = number_deck
        self.current_player_index = 0
        self.current_hand_index = 0
        self.dealer = []
        self.number_players = 0
        self.total_rewards = 0
        self.hand_players = {f'player_{i}': \
            {'hands': [], 'value': 0, 'nb_ace': 0, 'split': False,
             'bet': 0, 'current_player': self.current_player_index == i, 'hand_playing': 0, 'reward':0, 'blackjack': False} for i in range(6)}
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4 * self.number_deck 
        self.info = {card: self.deck.count(card) for card in set(self.deck)}
        self.len_deck = 13 * 4 * number_deck
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=0, high=31, shape=(2,), dtype=np.int32)
        self.observation_game = {
            "dealer": self.dealer,
            "players": self.hand_players,
            "info": self.info,
            "len_deck": self.len_deck
        }

    def reset():
        print('reset')
        # restart a new game and shuffle the cards
    
    def _get_obs(self):
        return self.observation_game()
    
    def value_hands(self, hands):
        """
        Calculates the value of a hand taking into account aces.
        
        Parameters:
        - hands: list of cards in the hand.
        
        Returns:
        - value: value of the hand.
        """
        value = 0
        num_aces = 0
        
        for card in hands:
            if card == 11:  
                num_aces += 1
                value += 11
            else:
                value += card
    
        while value > 21 and num_aces > 0:
            value -= 10 
            num_aces -= 1
        
        return value
    
    def play_dealer_hand(self):
        """
        Plays the dealer's hand according to the rules.
        """
        self.dealer_value = self.value_hands(self.dealer)
        
        while self.dealer_value < 17:
            self.dealer.append(self.deck.pop())
            self.dealer_value = self.value_hands(self.dealer)
        
    def player_vs_dealer(self, reward, player_value, dealer_value):
        """
        Determines the reward for a player based on the comparison of the player's hand value with the dealer's hand value.
        
        Parameters:
        - reward: reward to be updated based on the comparison of the player's hand value with the dealer's hand value.
        - player_value: value of the player's hand.
        - dealer_value: value of the dealer's hand.
        
        Returns:
        - reward: updated reward based on the comparison of the player's hand value with the dealer's hand value.
        """
        reward = 0
        if player_value > 21:
            reward = -self.hand_players[f'player_{self.current_player_index}']['bet']
        elif dealer_value > 21 or player_value > dealer_value:
            reward = self.hand_players[f'player_{self.current_player_index}']['bet']
        elif player_value == dealer_value:
            reward = 0
        else:
            reward = -self.hand_players[f'player_{self.current_player_index}']['bet']
        return reward
        

    def play_single_hand(self, action, hand):
        """
        Manages the transition to the next state for the player's current hand after an action.
        
        Parameters:
        - action: chosen action (HIT, STAND, SPLIT, etc.).
        - hand: the current hand on which the action is applied.
        
        Returns:
        - observation: observed state after the action
        - reward: reward obtained after the action
        - done: boolean indicating if the episode is over
        - truncated: boolean indicating if the episode was truncated
        """
        reward = 0
        dealer_playing = self.current_player_index == self.number_players
        next_player = False

        if not dealer_playing:

            if action == Actions.HIT:
                hand.append(self.deck.pop())
                value = self.value_hands(hand)
                if value < 21:
                    reward = (21 - value) / 21
                elif value == 21:
                    print("Value 21 reached, move to the next hand")
                    reward = (21 - value) / 21
                    next_player = True
                elif value > 21:
                    print("Value over 21 reached, move to the next hand")
                    reward = -self.hand_players[f'player_{self.current_player_index}']['bet']
                    next_player = True

            elif action == Actions.STAND:
                value = self.value_hands(hand)
                reward = (21 - value) / 21
                next_player = True

            elif action == Actions.SPLIT and len(hand) == 2 and hand[0] == hand[1]:
                if not self.hand_players[f'player_{self.current_player_index}']['split']:
                    self.handle_split() 
                else: 
                    #Deal with unpossibility to split with mask 
                    reward = -self.hand_players[f'player_{self.current_player_index}']['bet']

            elif action == Actions.DOUBLE:
                print("Double chosen, draw a card and move to the next player")
                hand.append(self.deck.pop())
                value = self.value_hands(hand)
                reward = (21 - value) / 21 \
                    if self.value_hands(hand) <= 21 else -self.hand_players[f'player_{self.current_player_index}']['bet']
                next_player = True

            # Move to the next hand or player as appropriate
            self.advance_hand_or_player(next_player)

            # Return the state and end information
            return self._get_obs(), reward, False, False
        else:
            # Handle the dealer's turn after all players have finished
            print("The dealer is now playing")
            self.play_dealer_hand()
            
            # Calculate the rewards for each player
            for i in range(self.number_players):
                player = f'player_{i}'
                if self.hand_players[player]['split']:
                    for hand in self.hand_players[player]['hands']:
                        reward = self.player_vs_dealer(reward, self.value_hands(hand), self.dealer_value)
                        self.total_rewards += reward
                else:
                    reward = self.player_vs_dealer(reward, self.value_hands(hand), self.dealer_value)
                    self.total_rewards += reward
            return self._get_obs(), self.total_rewards, False, False  

    def advance_hand_or_player(self, next_player):
        """
        Moves to the next hand for the current player or to the next player if all hands of the player have been played.
        """
        if self.current_hand_index < len(self.hand_players[f'player_{self.current_player_index}']['hands']) - 1:
            self.current_hand_index += 1  # Move to the next hand of the same player
            print(f"Move to the next hand for player {self.current_player_index}: hand {self.current_hand_index}")
        elif next_player:
            self.current_hand_index = 0  # Reset the hand index for the next player
            self.current_player_index += 1
            print(f"Move to the next player: player {self.current_player_index}")


    def handle_split(self):
        """
        Handles the case where the player chooses to split.
        """
        current_player = f'player_{self.current_player_index}'
        hand = self.hand_players[current_player]['hands'][self.current_hand_index]
        
        # Split the hand into two new hands with additional cards
        card1, card2 = hand
        new_hand1 = [card1, self.deck.pop()]
        new_hand2 = [card2, self.deck.pop()]
        
        # Update the list of hands to include the new hands from the split
        self.hand_players[current_player]['hands'][self.current_hand_index] = new_hand1
        self.hand_players[current_player]['hands'].insert(self.current_hand_index + 1, new_hand2)
        self.hand_players[current_player]['split'] = True
        print(f"Hand split for {current_player}: new hands {new_hand1} and {new_hand2}")


    def step(self, action):        
        """
        Takes an action and returns the results as observation, reward, and end state.
        
        Parameters:
        - action: action chosen by the agent.
        
        Returns:
        - observation: the state after the action
        - reward: reward following the action
        - done: indicates if the episode is over
        - truncated: indicates if the episode was truncated
        """
        current_hand = self.hand_players[f'player_{self.current_player_index}']['hands'][self.current_hand_index]
        new_state, reward, done, truncated = self.play_single_hand(action, self.value_hands(current_hand), current_hand)
        
        return new_state, reward, done, truncated

        
        
        
        
    
    
    
    
    
    
    
    
    
    # def initialize_hands(self):
    #     number_players = self.set_player()
    #     self.dealer = []
    #     for i in range(2):
    #         self.dealer.append(self.deck.pop(0))
    #         for i in range(number_players):
    #             card_hitten = self.deck.pop(0)
    #             self.hand_players[f'player_{i}']['hands'].append(card_hitten)
    #             self.hand_players[f'player_{i}']['value'] = self.value_hands(self.hand_players[f'player_{i}']['hands'])
    #             self.hand_players[f'player_{i}']['split'] = False
    #             self.hand_players[f'player_{i}']['nb_ace'] = self.hand_players[f'player_{i}']['hands'].count(11)  
         
    
    # def set_player(self):
    #     number_players = 0 
    #     while number_players < 1 or number_players > 7:
    #         number_players = int(input('How many players? '))
    #     for i in range(number_players):
    #         bet = 0
    #         while bet not in [5, 10, 25, 50, 75, 100]:
    #             bet = int(input(f'Player {i+1}, place your bet [5, 10, 25, 50, 75, 100]: '))
    #             self.hand_players[f'player_{i}']['bet'] = bet
    #             self.wallet -= bet
    #     return number_players