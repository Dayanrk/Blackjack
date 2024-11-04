import random

class BlackjackGame():

    def __init__(self,  number_deck):
        self.wallet = 1000
        self.number_deck = number_deck
        self.hand_players = {f'player_{i}': {'hands':[],'value':0, 'nb_ace':0, 'bet':0} for i in range(7)}
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4 * self.number_deck 
        self.info = {card: self.deck.count(card) for card in set(self.deck)}
        self.len_deck = 13 * 4 * number_deck
        self.initialize_deck()
        self.start_new_game()
        
    def initialize_deck(self):
        random.shuffle(self.deck)
        return self.deck

    def set_player(self):
        number_players = 0 
        while number_players < 1 or number_players > 7:
            number_players = int(input('How many players? '))
        for i in range(number_players):
            bet = 0
            while bet not in [5, 10, 25, 50, 75, 100]:
                bet = int(input(f'Player {i+1}, place your bet [5, 10, 25, 50, 75, 100]: '))
                self.hand_players[f'player_{i}']['bet'] = bet
                self.wallet -= bet
        return number_players
    
    def value_hands(self, hands):
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

    def initialize_hands(self):
        number_players = self.set_player()
        self.dealer = []
        for i in range(2):
            self.dealer.append(self.deck.pop(0))
            for i in range(number_players):
                card_hitten = self.deck.pop(0)
                self.hand_players[f'player_{i}']['hands'].append(card_hitten)
                self.hand_players[f'player_{i}']['value'] = self.value_hands(self.hand_players[f'player_{i}']['hands'])
                self.hand_players[f'player_{i}']['split'] = False
                self.hand_players[f'player_{i}']['nb_ace'] = self.hand_players[f'player_{i}']['hands'].count(11)  
        
    def compare_hands_with_dealer(self, player, hand):
        if self.value_hands(hand) > 21:
            print(f'{player} a perdu la main {hand} avec une valeur de {self.value_hands(hand)}')
        elif self.value_hands(self.dealer) > 21:
            print(f'{player} a gagné car le croupier a dépassé 21')
            self.wallet += 2 * self.hand_players[player]['bet']
        elif self.value_hands(hand) > self.value_hands(self.dealer):
            print(f'{player} a gagné la main {hand} avec une valeur de {self.value_hands(hand)}')
            self.wallet += 2 * self.hand_players[player]['bet']
        elif self.value_hands(hand) < self.value_hands(self.dealer):
            print(f'{player} a perdu la main {hand} avec une valeur de {self.value_hands(hand)}')
        else:
            print(f'{player} a égalisé la main {hand} avec une valeur de {self.value_hands(hand)}')
            self.wallet += self.hand_players[player]['bet']
        print(f'Wallet: {self.wallet}')
    def set_winner(self):
        while True: 
            if self.value_hands(self.dealer) < 17:
                self.dealer.append(self.deck.pop(0))
            elif self.value_hands(self.dealer) >= 17 and self.value_hands(self.dealer) <= 21:
                print('Dealer Stand!')
                print(f'Dealer hand: {self.dealer} with a value of {self.value_hands(self.dealer)}')
                break
            else:
                print(f'Dealer BUST with a value of {self.value_hands(self.dealer)}')
                break
        
        for player, hand_data in self.hand_players.items():
            if hand_data['hands'] == []:
                break
            hands = hand_data['hands']
            if isinstance(hands[0], list) and hands['split'] == True:
                for hand in hands:
                    self.compare_hands_with_dealer(player, hand)
            else: 
                self.compare_hands_with_dealer(player, hands)   
                
    
    def split(self, player, hand):
        card1, card2 = hand
        new_hand1 = [card1, self.deck.pop()] 
        new_hand2 = [card2, self.deck.pop()]
        self.hand_players[player]['split'] = True
        
        # Si c'est la première fois qu'on split pour ce joueur, on transforme 'hands' en liste de listes
        self.hand_players[player]['hands'] = [new_hand1, new_hand2]
        
        self.hand_players[player]['value'] = [self.value_hands(new_hand1), self.value_hands(new_hand2)]
        self.hand_players[player]['nb_ace'] = [new_hand1.count(11), new_hand2.count(11)]
        
        print(f'Après le split, {player} a les mains: {self.hand_players[player]["hands"]}')
        #playing all hand of the player
        for hand_index, hand in enumerate(self.hand_players[player]['hands']):
            print(hand)
            print(f'{player} joue la main {hand_index + 1}: {hand} avec une valeur de {self.value_hands(hand)}')
            self.play_single_hand(player, hand)
            print(f'Fin de la main {hand_index + 1}')
      
    def play_single_hand(self, player, hand):
        while True:
            print(f'{player}, voici ta main actuelle: {hand}')
            print(f'La main du croupier est: {self.dealer[0]}')
            
            # Propose des actions au joueur : Tirer (Hit), Rester (Stand), Split (si applicable)
            action = int(input('Choisissez une action: 0 pour Hit, 1 pour Stand, 2 pour Split: '))
            
            if action == 0:
                hand.append(self.deck.pop())  # Le joueur tire une carte
                hand_value = self.value_hands(hand)
                print(f'{player} a tiré une nouvelle carte, main actuelle: {hand}, valeur: {hand_value}')
                
                if hand_value > 21:
                    print(f'{player} a dépassé 21, BUST!')
                    break  # Si la main dépasse 21, le joueur perd cette main
                
                elif hand_value == 21:
                    print(f'{player} a atteint 21!')
                    break
            elif action == 1:
                print(f'{player} a décidé de rester avec une main de {hand}')
                break  # Le joueur reste et ne tire plus de cartes

            elif action == 2 and len(hand) == 2 and hand[0] == hand[1] and not self.hand_players[player]['split']:
                # Si le joueur décide de splitter et que les cartes sont identiques et que il n'a déja pas splitter
                self.split(player, hand)  # Appelle la fonction de split pour ce joueur
                break  # Après le split, on quitte cette main pour gérer les nouvelles mains
            
            else:
                print("Action invalide ou non disponible. Réessaye.")
               
    def time_to_shuffle(self):
        if len(self.deck) < self.len_deck / 2:
            self.deck = self.initialize_deck()
            print('Shuffling the deck')  
            print('End Episode')
    
    def start_new_game(self):
        while True:
            self.initialize_hands() 
            for player, hand_data in self.hand_players.items():
                if hand_data['hands'] == []:
                    break
                hands = hand_data['hands'] 
                bet = hand_data['bet']
                if isinstance(hands[0], list) and hands['split'] == True:  
                    for hand_index, hand in enumerate(hands):
                        print(f'{player} joue la main {hand_index + 1}: {hand} avec une valeur de {self.value_hands(hand)}')
                        self.hand_players[player]['bet'] = [bet, bet]
                        self.play_single_hand(player, hand)
                        print(f'Fin de la main {hand_index + 1}')
                else:
                    print(f'{player} joue la main: {hands} avec une valeur de {self.value_hands(hands)}')
                    self.play_single_hand(player, hands)
                    print(f'Fin de la main')
            
            self.set_winner()
            self.time_to_shuffle() 
        
env = BlackjackGame(6)