#!/usr/bin/env python3
"""
Simple Endless Runner Game - Dino Runner
Inspired by the Chrome offline dinosaur game
"""

import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 300
GROUND_HEIGHT = 50
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dino Runner")
clock = pygame.time.Clock()

class Dino:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT - GROUND_HEIGHT - 50
        self.width = 40
        self.height = 50
        self.velocity = 0
        self.gravity = 1
        self.jump_strength = -15
        self.is_jumping = False
        self.color = GREEN
        
    def jump(self):
        if not self.is_jumping:
            self.velocity = self.jump_strength
            self.is_jumping = True
    
    def update(self):
        # Apply gravity
        self.velocity += self.gravity
        self.y += self.velocity
        
        # Ground collision
        if self.y > SCREEN_HEIGHT - GROUND_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - GROUND_HEIGHT - self.height
            self.velocity = 0
            self.is_jumping = False
    
    def draw(self):
        # Draw dino (simple rectangle for now)
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Draw eyes
        pygame.draw.circle(screen, BLACK, (self.x + 30, self.y + 15), 3)
        # Draw legs
        pygame.draw.rect(screen, self.color, (self.x, self.y + self.height - 10, 10, 15))
        pygame.draw.rect(screen, self.color, (self.x + 30, self.y + self.height - 10, 10, 15))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Cactus:
    def __init__(self):
        self.width = 20
        self.height = random.randint(40, 80)
        self.x = SCREEN_WIDTH
        self.y = SCREEN_HEIGHT - GROUND_HEIGHT - self.height
        self.speed = 8
        
    def update(self):
        self.x -= self.speed
        
    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, self.height))
        # Add some spikes
        for i in range(0, self.height, 10):
            pygame.draw.polygon(screen, (0, 150, 0), [
                (self.x - 5, self.y + i),
                (self.x + self.width + 5, self.y + i),
                (self.x + self.width // 2, self.y + i - 10)
            ])
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Game:
    def __init__(self):
        self.dino = Dino()
        self.cacti = []
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_over = False
        self.font = pygame.font.SysFont('Arial', 24)
        self.spawn_timer = 0
        self.spawn_interval = 60  # frames
        self.base_speed = 8
        self.speed_increase_interval = 2  # score points
        self.last_speed_increase = 0
        self.current_speed = self.base_speed
        self.max_speed = 20
        
    def spawn_cactus(self):
        if self.spawn_timer <= 0 and len(self.cacti) < 3:
            self.cacti.append(Cactus())
            self.spawn_timer = self.spawn_interval
        else:
            self.spawn_timer -= 1
    
    def update_difficulty(self):
        # Increase speed as score increases
        if self.score - self.last_speed_increase >= self.speed_increase_interval:
            if self.current_speed < self.max_speed:
                self.current_speed += 1
                self.last_speed_increase = self.score
                
                # Also make cacti spawn more frequently as game gets harder
                # But do this less frequently than speed increases
                if self.score % 10 == 0 and self.spawn_interval > 30:
                    self.spawn_interval = max(30, self.spawn_interval - 1)
        
        # Update all cacti speeds to current speed
        for cactus in self.cacti:
            cactus.speed = self.current_speed
    
    def update(self):
        if self.game_over:
            return
            
        self.dino.update()
        
        # Update difficulty based on score
        self.update_difficulty()
        
        # Update cacti
        for cactus in self.cacti[:]:
            cactus.update()
            if cactus.x < -cactus.width:
                self.cacti.remove(cactus)
                self.score += 1
        
        self.spawn_cactus()
        
        # Check collisions
        dino_rect = self.dino.get_rect()
        for cactus in self.cacti:
            if dino_rect.colliderect(cactus.get_rect()):
                self.game_over = True
                self.update_high_score()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        # Restart game
                        self.__init__()
                    else:
                        self.dino.jump()
                elif event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def load_high_score(self):
        try:
            with open('high_score.txt', 'r') as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError):
            return 0
    
    def save_high_score(self, score):
        with open('high_score.txt', 'w') as file:
            file.write(str(score))
    
    def update_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score(self.high_score)
    
    def draw(self):
        # Clear screen
        screen.fill(WHITE)
        
        # Draw ground
        pygame.draw.rect(screen, GRAY, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))
        
        # Draw dino
        self.dino.draw()
        
        # Draw cacti
        for cactus in self.cacti:
            cactus.draw()
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        # Draw high score
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, BLACK)
        screen.blit(high_score_text, (SCREEN_WIDTH - 200, 10))
        
        # Draw current speed indicator
        speed_text = self.font.render(f"Speed: {self.current_speed}", True, (50, 50, 200))
        screen.blit(speed_text, (SCREEN_WIDTH//2 - 50, 10))
        
        # Draw game over message
        if self.game_over:
            game_over_text = self.font.render("GAME OVER - Press SPACE to restart", True, (200, 0, 0))
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)
            
            # Show final score
            final_score_text = self.font.render(f"Your Score: {self.score}", True, (200, 0, 0))
            final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            screen.blit(final_score_text, final_score_rect)
        else:
            # Draw instructions
            instructions = self.font.render("Press SPACE to jump", True, BLACK)
            screen.blit(instructions, (10, 50))
        
        pygame.display.flip()

def main():
    game = Game()
    
    # Main game loop
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()