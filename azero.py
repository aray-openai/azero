#!/usr/bin/env python

import numpy as np
from collections import defaultdict

NUM_EPOCHS = 100
GAMES_PER_UPDATE = 100
SIMS_PER_SEARCH = 100
C_PUCT = 1.5  # PUCT coefficient controlling exploration (see NOTES.md)


class Tree:
    ''' Data structure used during search step '''
    def isLeaf(self):
        return hasattr(self, 'children')

    def expand(self, probs, value):
        ''' Expand tree with results of model '''
        self.children = defaultdict(Tree)  # Map from action -> sub-Tree()
        self.prior = probs
        self.value = value
        self.T = 0  # Total of all N(s, a) of children
        self.N = np.zeros(len(probs))
        self.W = np.zeros(len(probs))
        self.Q = np.zeros(len(probs))

    def select(self):
        ''' Select and upper-confidence-bound move and return action, child '''
        U = C_PUCT * np.sqrt(self.T) * self.prior / (1 + self.N)
        Q = np.where(self.N > 0, self.W / self.N, 0)
        action = np.argmax(Q + U)
        return action, self.children[action]

    def backup(self, action, value):
        ''' Backup results of a simulation game '''
        self.T += 1
        self.N[action] += 1
        self.W[action] += value
        self.Q[action] = self.W[action] / self.N[action]

    def probs(self):
        ''' Return move probabilities '''
        return []


class AlphaZero:
    def __init__(self, game, model):
        ''' Train a model to play a game with the AlphaZero algorithm '''
        self.game = game
        self.model = model

    def simulate(self, tree):
        ''' Simulate a game by traversing tree '''
        if tree.isLeaf():
            probs, value = self.model.model(tree.state)
            tree.expand(probs, value)
            return value
        action, child = tree.select()
        value = self.simulate(child)
        tree.backup(action, value)
        return value

    def search(self, state, tree):
        ''' MCTS to generate move probabilities for a state '''
        [self.simulate(tree, state) for _ in range(SIMS_PER_SEARCH)]
        return tree.probs(), tree

    def sample(self, state, probs):
        ''' Sample a valid action from a vector of action probabilities '''
        masked = probs * self.game.valid(state)
        return np.random.choice(len(masked), p=masked / np.sum(masked))

    def play(self):
        ''' Self-play a game, return probabilities and outcome '''
        trajectory = []  # List of pairs of (state, probabilities from search)
        state = self.game.start()
        tree = Tree()
        while state is not None:
            probs, tree = self.search(state, tree)
            trajectory.append((state, probs))
            action = self.sample(state, probs)
            state, outcome = self.game.step(state, action)
            tree = tree.children[tree]  # Re-use subtree for chosen action
        return trajectory, outcome

    def epoch(self):
        for _ in range(NUM_EPOCHS):
            games = [self.play() for _ in range(GAMES_PER_UPDATE)]
            self.model.update(games)