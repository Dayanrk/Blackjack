import gym
import numpy as np
class MultiPartiesEnv(gym.Wrapper):
    def __init__(self, env=None, min_players=1, max_players=6, cards_threshold=0.5):
        super(MultiPartiesEnv, self).__init__(env)
        self.min_players = min_players
        self.max_players = max_players
        self.cards_threshold = cards_threshold
        self.current_player_count = None
        self.cards_dealt = 0  # Nombre de cartes distribuées

    def reset(self):
        # Réinitialiser l'environnement et les compteurs
        obs = self.env.reset()
        self.cards_dealt = 0
        
        # Démarrer une nouvelle partie
        self.start_new_partie()
        
        return obs

    def start_new_partie(self):
        """Lance une nouvelle partie en demandant à l'agent combien de joueurs il veut."""
        self.current_player_count = self.agent_select_player_count()
        
        # Configurer le nombre de joueurs pour cette partie
        self.env.set_player_count(self.current_player_count)

    def step(self, action):
        # Effectuer une action dans l'environnement
        obs, reward, done, info = self.env.step(action)
        
        # Mettre à jour le nombre de cartes distribuées
        self.cards_dealt += info.get('cards_dealt_this_turn', 0)
        
        # Vérifier si la partie actuelle est terminée
        if self.cards_dealt >= self.cards_threshold * self.env.total_cards:
            # Si la moitié des cartes sont distribuées, démarrer une nouvelle partie
            self.cards_dealt = 0
            self.start_new_partie()
        
        return obs, reward, done, info

    def agent_select_player_count(self):
        # Logique pour que l'agent sélectionne le nombre de joueurs (peut être remplacée par une logique d'agent réelle)
        return np.random.randint(self.min_players, self.max_players + 1)
