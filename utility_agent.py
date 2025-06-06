"""
Utility-Based Agent implementation
"""
from typing import Any, Dict, List, Tuple
import random

from agent import Agent


class UtilityBasedAgent(Agent):
    """
    A utility-based agent that chooses actions based on their expected utility.
    """
    
    def __init__(self, name: str = "UtilityBasedAgent", exploration_rate: float = 0.1):
        """
        Initialize the agent.
        
        Args:
            name: A name for the agent
            exploration_rate: Probability of choosing a random action (exploration)
        """
        super().__init__(name)
        self.percept = None
        self.position = None
        self.model = {}  # Maps positions to cell contents
        self.utilities = {}  # Maps positions to utility values
        self.exploration_rate = exploration_rate
        self.discount_factor = 0.9  # For utility calculations
        self.goal_positions = []  # Known goal positions
        self.last_position = None
        self.current_action = None
        self.visit_counts = {}  # For visualization
        
    def perceive(self, percept: Any) -> None:
        """
        Process a percept from the environment and update the internal model.
        
        Args:
            percept: The percept received from the environment
        """
        self.percept = percept
        self.last_position = self.position
        
        # Update position
        if "position" in percept:
            self.position = percept["position"]
            
            # Track visit count for visualization
            self.visit_counts[self.position] = self.visit_counts.get(self.position, 0) + 1
            
        # Update the model with cell content
        if "cell_content" in percept and self.position:
            self.model[self.position] = percept["cell_content"]
            
            # If it's a goal, add to goal positions
            if percept["cell_content"] == 2:  # GOAL
                if self.position not in self.goal_positions:
                    self.goal_positions.append(self.position)
                    
        # Update the model with information about adjacent cells
        if "adjacents" in percept and self.position:
            x, y = self.position
            if "up" in percept["adjacents"]:
                self.model[(x, y-1)] = percept["adjacents"]["up"]
            if "down" in percept["adjacents"]:
                self.model[(x, y+1)] = percept["adjacents"]["down"]
            if "left" in percept["adjacents"]:
                self.model[(x-1, y)] = percept["adjacents"]["left"]
            if "right" in percept["adjacents"]:
                self.model[(x+1, y)] = percept["adjacents"]["right"]
                
        # Update utilities after each move
        self.update_utilities()
        
    def update_utilities(self) -> None:
        """
        Update the utility values for known positions.
        Uses a simple form of value iteration from reinforcement learning.
        """
        # Initialize utilities for all known positions
        for pos in self.model:
            if pos not in self.utilities:
                # Default utility is negative for obstacles, positive for goals, zero otherwise
                if self.model[pos] == 1:  # OBSTACLE
                    self.utilities[pos] = -10.0
                elif self.model[pos] == 2:  # GOAL
                    self.utilities[pos] = 10.0
                else:
                    self.utilities[pos] = 0.0
                    
        # If no goals are known, we can't calculate meaningful utilities
        if not self.goal_positions:
            return
            
        # Update utilities through value iteration (multiple iterations for better convergence)
        for _ in range(5):  # Reduced from 30 to speed up processing
            new_utilities = self.utilities.copy()
            
            for pos in self.model:
                if self.model[pos] == 1:  # Skip obstacles
                    continue
                if pos in self.goal_positions:  # Goals have fixed utility
                    continue
                    
                # Calculate utility based on neighbors
                x, y = pos
                neighbors = [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]
                max_utility = float('-inf')
                
                for neighbor in neighbors:
                    # Skip if neighbor is unknown or an obstacle
                    if neighbor not in self.model or self.model[neighbor] == 1:
                        continue
                        
                    # Get utility of neighbor
                    neighbor_utility = self.utilities.get(neighbor, 0.0)
                    
                    # Calculate utility of moving to this neighbor
                    reward = -0.1  # Step cost
                    if neighbor in self.goal_positions:
                        reward = 10.0  # Goal reward
                    
                    utility = reward + self.discount_factor * neighbor_utility
                    
                    # Track maximum utility
                    if utility > max_utility:
                        max_utility = utility
                        
                # If no valid neighbors, keep current utility
                if max_utility != float('-inf'):
                    new_utilities[pos] = max_utility
                    
            # Update utilities
            self.utilities = new_utilities
            
    def get_action_utility(self, action: str) -> float:
        """
        Calculate the utility of taking an action.
        
        Args:
            action: The action to evaluate
            
        Returns:
            The estimated utility of the action
        """
        if not self.position:
            return 0.0
            
        x, y = self.position
        next_pos = None
        
        # Determine next position based on action
        if action == "up":
            next_pos = (x, y-1)
        elif action == "down":
            next_pos = (x, y+1)
        elif action == "left":
            next_pos = (x-1, y)
        elif action == "right":
            next_pos = (x+1, y)
            
        # If next position is unknown or an obstacle, return low utility
        if next_pos not in self.model:
            return -1.0  # Unknown cell penalty (increased from -2.0)
        if self.model[next_pos] == 1:  # OBSTACLE
            return -5.0  # Obstacle penalty (reduced from -10.0)
            
        # Return utility of next position
        return self.utilities.get(next_pos, 0.0)
        
    def decide(self) -> Any:
        """
        Decide on an action based on utilities.
        
        Returns:
            An action to be performed
        """
        # If at goal, stay there
        if self.position in self.goal_positions:
            self.current_action = None
            return None
            
        # Exploration: occasionally take a random action
        if random.random() < self.exploration_rate:
            # Focus on valid actions only
            actions = ["up", "down", "left", "right"]
            valid_actions = []
            
            for action in actions:
                x, y = self.position
                if action == "up":
                    next_pos = (x, y-1)
                elif action == "down":
                    next_pos = (x, y+1)
                elif action == "left":
                    next_pos = (x-1, y)
                elif action == "right":
                    next_pos = (x+1, y)
                    
                if next_pos not in self.model or self.model[next_pos] != 1:  # Not an obstacle
                    valid_actions.append(action)
                    
            if valid_actions:
                self.current_action = random.choice(valid_actions)
            else:
                # If all directions are obstacles, try random anyway
                self.current_action = random.choice(actions)
            
            return self.current_action
            
        # Otherwise, choose the action with highest utility
        actions = ["up", "down", "left", "right"]
        utilities = [self.get_action_utility(action) for action in actions]
        
        # Get all actions with the maximum utility
        max_utility = max(utilities)
        best_actions = [action for action, utility in zip(actions, utilities) 
                       if utility == max_utility]
        
        # Choose randomly among the best actions
        self.current_action = random.choice(best_actions)
        
        return self.current_action
        
    def act(self) -> Any:
        """
        Execute the decided action.
        
        Returns:
            The action performed
        """
        return self.current_action