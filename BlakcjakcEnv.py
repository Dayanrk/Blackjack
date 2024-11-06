import gym 
from gym import spaces
from enum import Enum
import numpy as np
import random

class Actions(Enum):
    HIT = 0
    STAND = 1
    SPLIT = 2
    DOUBLE = 3
    
class BlackjackEnv(gym.Env):
    
    def __init__(self, number_deck):
        super().__init__()
        self.number_deck = number_deck
        self.current_player_index = 0
        self.current_hand_index = 0
        self.dealer = []
        self.wallet = 1000
        self.number_players = 0
        self.total_rewards = 0
        self.hand_players = {f'player_{i}': \
            {'hands': [], 'value': 0, 'nb_ace': 0, 'split': False,
             'bet': 0, 'current_player': self.current_player_index == i, 'hand_playing': 0, 'reward':0, 'blackjack': False} for i in range(6)}
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4 * self.number_deck 
        self.info = {card: self.deck.count(card) for card in set(self.deck)}
        self.len_deck = 13 * 4 * number_deck
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Dict({
            "dealer":  spaces.Dict({
                'value': spaces.Box(low=0, high=31, shape=(1,), dtype=np.int32),
                #hand represent card hand 
                'hand': spaces.Box(low=0, high=11, shape=(10,), dtype=np.int32)
                }),
            "len_deck": spaces.Discrete(self.len_deck + 1),  # Nombre de cartes restantes dans le deck
            "info": spaces.Dict({  # Comptage des cartes restantes
                card: spaces.Discrete(52 * self.number_deck + 1) for card in set(self.deck)
            }),
            "players": spaces.Dict({  # Informations détaillées pour chaque joueur
                f'player_{i}': spaces.Dict({
                    "hands": spaces.Box(low=0, high=31, shape=(5,), dtype=np.int32),  # Valeur de chaque main (on suppose jusqu'à 5 mains max)
                    "value": spaces.Box(low=0, high=31, shape=(1,), dtype=np.int32),  # Valeur de la main active
                    "nb_ace": spaces.Discrete(10),  # Nombre d'as (jusqu'à 4 ou 5 possibles par main)
                    "split": spaces.Discrete(2),  # 1 si la main est splittée, sinon 0
                    "bet": spaces.Box(low=0, high=500, shape=(1,), dtype=np.int32),  # Montant du pari (peut être ajusté selon les limites)
                    "current_player": spaces.Discrete(2),  # Indique si c'est le joueur actif
                    "hand_playing": spaces.Discrete(2),  # Index de la main active (jusqu'à 2)
                    "blackjack": spaces.Discrete(2)  # 1 si le joueur a un blackjack, sinon 0
                }) for i in range(6) # Prend en charge jusqu'à 6 joueurs
            }),
            "wallet": spaces.Box(low=0, high=1e6, shape=(1,), dtype=np.float32)
        })
        
        self.observation_game =  {
            "dealer": {'value': 0, 'hand': []},
            "len_deck": self.len_deck,
            "info": self.info,
            "players": self.hand_players,
            "wallet": self.wallet
        }

    def shuffle_deck(self):
        """
        Mélange le deck de cartes.
        """
        random.shuffle(self.deck)
        return self.deck
    
    def time_to_shuffle(self):
        return len(self.deck) < self.len_deck // 2

    def reset():
        print('reset')
    
    def _get_obs(self):
        return self.observation_game
    
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
        if self.time_to_shuffle(): 
            self.shuffle_deck()
        
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
        
    
    def initialize_new_game(self):    
        """
        Initializes a new game by shuffling the deck, dealing the initial hands, and setting the initial player.

        """
        for i in range(2):
            for player in self.hand_players:
                # distribuer carte de chaque joueur 
                self.hand_players[player]['hands'].append(self.deck.pop())
            self.dealer.append(self.deck.pop())
                
    def end_round(self):
        """
        Calcule la récompense finale pour chaque joueur, renvoie l'observation finale et réinitialise le jeu pour une nouvelle manche.
        """
        self.total_rewards = 0  # Réinitialise les récompenses totales pour la manche
        
        # Calcule les récompenses pour chaque joueur en fonction de la main du croupier
        self.play_dealer_hand()  # Le dealer joue sa main finale
        
        for i in range(self.number_players):
            player_key = f'player_{i}'
            player_info = self.hand_players[player_key]
            
            # Calcule les gains pour chaque main (s'il y a eu un split, chaque main est évaluée individuellement)
            if player_info['split']:
                for hand in player_info['hands']:
                    reward = self.player_vs_dealer(0, self.value_hands(hand), self.dealer_value)
                    self.total_rewards += reward
            else:
                reward = self.player_vs_dealer(0, player_info['value'], self.dealer_value)
                self.total_rewards += reward
            
            # Ajuste le portefeuille (wallet) en fonction du gain ou de la perte
            self.wallet += self.total_rewards

            actual_state = self._get_obs()
        # Prépare pour une nouvelle manche
        self.reset_game()  # Méthode pour réinitialiser les mains et le deck
        return actual_state, self.total_rewards, True, False
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
            return self._get_obs(), self.total_rewards, True  , False  

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

    def get_action_mask(self):
        """
        Crée un masque binaire pour les actions valides et invalides en fonction de l’état actuel de la main du joueur.
        """
        mask = np.ones(self.action_space.n)  # Par défaut, toutes les actions sont valides
        
        # Récupérer la main actuelle du joueur
        current_hand = self.hand_players[f'player_{self.current_player_index}']['hands'][self.current_hand_index]
        value = self.value_hands(current_hand)
        
        # Vérifier les conditions d’invalidité pour chaque action
        if value >= 21:
            # Si la main est 21 ou plus, "HIT" et "DOUBLE" sont invalides
            mask[Actions.HIT.value] = 0
            mask[Actions.DOUBLE.value] = 0

        # "SPLIT" est invalide si les cartes sont différentes ou si le joueur a déjà splitté
        if len(current_hand) != 2 or current_hand[0] != current_hand[1] or self.hand_players[f'player_{self.current_player_index}']['split']:
            mask[Actions.SPLIT.value] = 0

        # "DOUBLE" peut être restreint aux cas où le joueur n’a pas encore tiré de cartes supplémentaires
        if len(current_hand) > 2:
            mask[Actions.DOUBLE.value] = 0
    
        return mask

    def step(self, action):
        """
        Exécute une action valide et retourne les résultats.
        """
        # Appliquer le masque d’actions
        mask = self.get_action_mask()

        # Vérifier si l’action choisie est valide
        if mask[action] == 0:
            # Si l'action est invalide, appliquer une pénalité ou ignorer l'action
            reward = -5  # Pénalité pour l’action invalide
            print("Action invalide choisie.")
            return self._get_obs(), reward, False, False

        # Si l'action est valide, exécute la main normalement
        current_hand = self.hand_players[f'player_{self.current_player_index}']['hands'][self.current_hand_index]
        new_state, reward, done, truncated = self.play_single_hand(action, current_hand)

        return new_state, reward, done, truncated