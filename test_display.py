#!/usr/bin/env python3
"""
Visual Test - Bouncing Ball Demo

Demonstrates that the TFT display can handle smooth animations.
Run this to verify display is working before full Tiny Programmer setup.
"""

import os
import sys
import time
import math

# Try to set up framebuffer for Pi
try:
    os.environ["SDL_VIDEODRIVER"] = "fbcon"
    os.environ["SDL_FBDEV"] = "/dev/fb1"
except:
    pass

import pygame

# Display settings (Waveshare 4inch RPi LCD A)
WIDTH = 480
HEIGHT = 320
FPS = 30

# Colors (retro green terminal style)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)


def main():
    """Run bouncing ball demo."""
    
    # Initialize pygame
    pygame.init()
    
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    except Exception as e:
        print(f"Framebuffer failed: {e}")
        print("Trying windowed mode...")
        os.environ.pop("SDL_VIDEODRIVER", None)
        os.environ.pop("SDL_FBDEV", None)
        pygame.quit()
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    pygame.display.set_caption("Tiny Programmer - Display Test")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    
    # Load font
    try:
        font = pygame.font.SysFont("DejaVu Sans Mono", 14)
        small_font = pygame.font.SysFont("DejaVu Sans Mono", 12)
    except:
        font = pygame.font.Font(None, 20)
        small_font = pygame.font.Font(None, 16)
    
    # Ball properties
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    ball_radius = 15
    ball_dx = 4
    ball_dy = 3
    
    # Trail effect
    trail = []
    max_trail = 20
    
    running = True
    frame_count = 0
    start_time = time.time()
    
    print("Display test running. Press ESC or Ctrl+C to exit.")
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Update ball position
        ball_x += ball_dx
        ball_y += ball_dy
        
        # Bounce off walls
        if ball_x - ball_radius < 0 or ball_x + ball_radius > WIDTH:
            ball_dx = -ball_dx
        if ball_y - ball_radius < 0 or ball_y + ball_radius > HEIGHT - 40:  # Leave room for status
            ball_dy = -ball_dy
        
        # Keep in bounds
        ball_x = max(ball_radius, min(WIDTH - ball_radius, ball_x))
        ball_y = max(ball_radius, min(HEIGHT - 40 - ball_radius, ball_y))
        
        # Add to trail
        trail.append((ball_x, ball_y))
        if len(trail) > max_trail:
            trail.pop(0)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw trail
        for i, (tx, ty) in enumerate(trail):
            alpha = int(255 * (i / max_trail) * 0.3)
            trail_color = (0, alpha, 0)
            pygame.draw.circle(screen, trail_color, (int(tx), int(ty)), ball_radius - 2)
        
        # Draw ball
        pygame.draw.circle(screen, GREEN, (int(ball_x), int(ball_y)), ball_radius)
        pygame.draw.circle(screen, DARK_GREEN, (int(ball_x), int(ball_y)), ball_radius - 3)
        
        # Draw status bar
        status_rect = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, (0, 30, 0), status_rect)
        pygame.draw.line(screen, GREEN, (0, HEIGHT - 40), (WIDTH, HEIGHT - 40), 1)
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        actual_fps = frame_count / elapsed if elapsed > 0 else 0
        
        # Status text
        status_text = f"STATE: display_test · FPS: {actual_fps:.1f}"
        text_surface = font.render(status_text, True, GREEN)
        screen.blit(text_surface, (8, HEIGHT - 32))
        
        info_text = "Tiny Programmer v0.1 - Press ESC to exit"
        info_surface = small_font.render(info_text, True, DARK_GREEN)
        screen.blit(info_surface, (8, HEIGHT - 16))
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    print(f"\nTest complete. Average FPS: {actual_fps:.1f}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        pygame.quit()
