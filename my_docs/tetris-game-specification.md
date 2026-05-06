# Tetris Game Specification Document

**Version:** 1.0  
**Date:** April 29, 2026  
**Status:** Requirements Analysis Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Core Mechanics](#core-mechanics)
3. [Scoring System](#scoring-system)
4. [Level Progression](#level-progression)
5. [Game Controls](#game-controls)
6. [UI/UX Features](#uiux-features)
7. [Game State Management](#game-state-management)
8. [Acceptance Criteria](#acceptance-criteria)

---

## Overview

This document defines the complete specification for a classic Tetris game implementation. The game follows traditional Tetris rules with modern enhancements including next piece preview, smooth animations, and progressive difficulty scaling.

### Target Platforms
- Desktop (Windows/Linux/macOS)
- Web browser compatible
- Terminal/console interface capable

### Technical Requirements
- Language: Python (recommended) or equivalent
- Frame rate: Minimum 60 FPS during gameplay
- Input latency: < 50ms response time

---

## Core Mechanics

### 2.1 Game Board

| Property | Value | Description |
|----------|-------|-------------|
| Grid Width | 10 cells | Horizontal playing area |
| Grid Height | 20 cells | Vertical playing area (including hidden rows above visible area) |
| Cell Size | Configurable | Typically 30x30 pixels minimum |
| Boundary Walls | Solid | Left, right, and bottom edges are immovable |

### 2.2 Tetromino Definitions

The game features exactly 7 unique tetromino shapes, each composed of 4 blocks:

#### 2.2.1 Shape Specifications

```
I-Tetromino (Linear)        J-Tetromino (Corner)       L-Tetromino (Reverse Corner)
   []                           []                          []
[] [] []                       [] [] []                    [] [] []
(Initial orientation)          (Initial orientation)       (Initial orientation)

O-Tetromino (Square)          S-Tetromino (Zigzag Right)   T-Tetromino (Tee)
   [] []                         [][]                         []
   [] []                        [][]                         [] []
                                 (Initial orientation)       (Initial orientation)

Z-Tetromino (Zigzag Left)
[][]
 [][]
(Initial orientation)
```

#### 2.2.2 Color Assignments

| Tetromino | RGB Color | Hex Code |
|-----------|-----------|----------|
| I (Cyan) | (0, 255, 255) | #00FFFF |
| J (Blue) | (0, 0, 255) | #0000FF |
| L (Orange) | (255, 165, 0) | #FFA500 |
| O (Yellow) | (255, 255, 0) | #FFFF00 |
| S (Green) | (0, 255, 0) | #00FF00 |
| T (Purple) | (128, 0, 128) | #800080 |
| Z (Red) | (255, 0, 0) | #FF0000 |

#### 2.2.3 Rotation System

- **Wall Kick System**: Basic wall kicks implemented
  - If rotation would place block outside grid, attempt to shift position
  - Maximum 2 attempts left/right per rotation
  - If no valid position exists, rotation is blocked

- **Rotation Directions**
  - Clockwise rotation (primary)
  - Counter-clockwise rotation (optional enhancement)

### 2.3 Piece Movement

| Action | Speed/Behavior | Description |
|--------|----------------|-------------|
| Soft Drop | Instant | Move down 1 cell per key press (score: +1 per cell) |
| Hard Drop | Immediate | Lock piece in current position (score: +2 per cell fallen) |
| Natural Fall | Level-dependent | Automatic downward movement at set intervals |
| Side Move | Instant | Move left/right one cell per input |
| Rotation | Instant | Rotate 90 degrees clockwise |

### 2.4 Spawning Rules

- New pieces spawn at top-center of the board (columns 4-7 depending on shape)
- Spawn delay: 0.5 seconds before player control activates (prevents instant death)
- Spawn position checked against existing blocks (game over if blocked)

---

## Scoring System

### 3.1 Line Clear Points

| Lines Cleared | Base Score Multiplier | Description |
|---------------|----------------------|-------------|
| 1 line | 100 x Level | Single |
| 2 lines | 300 x Level | Double |
| 3 lines | 500 x Level | Triple |
| 4 lines | 800 x Level | Tetris |
| 0 lines | 0 | No clear |

### 3.2 Movement Points

| Action | Points |
|--------|--------|
| Soft Drop (per cell) | 1 |
| Hard Drop (per cell fallen) | 2 |
| Piece Rotation | 0 |
| Piece Lock | 0 |

### 3.3 Total Score Calculation

```
Total Score = Line Clear Points + Drop Points

Line Clear Points = Base Multiplier × Current Level
Drop Points = Cells Moved × Points Per Cell
```

### 3.4 High Score Tracking

- Local high score persisted between sessions
- High score stored in configuration file
- Display current score and high score on-screen

---

## Level Progression

### 4.1 Level Advancement

| Level Threshold | Formula | Description |
|-----------------|---------|-------------|
| Start at Level | 1 | Game begins at level 1 |
| Lines Required per Level | 10 × Current Level | Lines cleared determines level up |

**Example Progression:**
- Level 1 → 2: Requires 10 lines
- Level 2 → 3: Requires 10 additional lines (20 total)
- Level 3 → 4: Requires 10 additional lines (30 total)
- And so on...

### 4.2 Maximum Levels

- Maximum level: 15 (or configurable)
- At maximum level, speed remains constant but scoring continues

### 4.3 Level Reset Conditions

- New game: Reset to Level 1
- Game over: Reset to Level 1 on restart

---

## Speed Increase

### 5.1 Drop Speed by Level

| Level | Interval (frames at 60FPS) | Interval (milliseconds) | Frames Per Second |
|-------|---------------------------|------------------------|-------------------|
| 1 | 48 frames | 800ms | ~1.25 drops/sec |
| 2 | 42 frames | 700ms | ~1.43 drops/sec |
| 3 | 36 frames | 600ms | ~1.67 drops/sec |
| 4 | 30 frames | 500ms | ~2.0 drops/sec |
| 5 | 24 frames | 400ms | ~2.5 drops/sec |
| 6 | 21 frames | 350ms | ~2.86 drops/sec |
| 7 | 18 frames | 300ms | ~3.33 drops/sec |
| 8 | 15 frames | 250ms | ~4.0 drops/sec |
| 9 | 12 frames | 200ms | ~5.0 drops/sec |
| 10 | 10 frames | 167ms | ~6.0 drops/sec |
| 11 | 8 frames | 133ms | ~7.5 drops/sec |
| 12 | 7 frames | 117ms | ~8.6 drops/sec |
| 13 | 6 frames | 100ms | ~10 drops/sec |
| 14 | 5 frames | 83ms | ~12 drops/sec |
| 15+ | 5 frames | 83ms | ~12 drops/sec (max speed) |

### 5.2 Speed Formulas

```
Base Interval = 800ms
Speed Decrement = 50ms per level (levels 1-8)
Minimum Interval = 83ms
```

**Formula:** `CurrentInterval = max(800 - (Level - 1) * 50, 83)`

---

## Game Controls

### 6.1 Primary Controls

| Action | Key Binding | Alternative | Description |
|--------|-------------|-------------|-------------|
| Move Left | Arrow Left / A | | Shift piece left |
| Move Right | Arrow Right / D | | Shift piece right |
| Soft Drop | Arrow Down / S | | Accelerate downward movement |
| Hard Drop | Space Bar | W | Instant drop to bottom |
| Rotate Clockwise | Arrow Up / X | Q | Rotate piece 90° clockwise |
| Rotate Counter-Clockwise | Z | C | Rotate piece 90° counter-clockwise (optional) |
| Pause/Resume | P | Enter | Toggle game pause state |
| Start/New Game | Enter | N | Start new game session |
| Quit | Esc | Q | Exit application |

### 6.2 Control Behaviors

#### 6.2.1 Repetition Handling
- Hold duration for auto-repeat: Initial 170ms, repeat every 50ms
- Prevents input flooding
- Smooth continuous movement when keys held

#### 6.2.3 Input Buffering
- 5-frame input buffer for late inputs near landing
- Allows player to make last-second adjustments

#### 6.2.3 Lock Delay
- When piece touches ground: 500ms grace period
- During grace period, movement/rotation still allowed
- Grace period resets if piece moves horizontally
- After grace period expires, piece locks permanently

---

## UI/UX Features

### 7.1 Next Piece Preview

**Requirements:**
- Display next 1-3 upcoming pieces
- Position: Right side of main game board
- Scale: Same as main game cells
- Color: Match assigned tetromino color
- Background: Semi-transparent panel

**Visual Layout:**
```
┌─────────────┬─────────────────┐
│             │  NEXT PIECES    │
│             │ ┌───────┐       │
│    MAIN     │ │   ?   │       │
│   BOARD     │ ├───────┤       │
│   AREA      │ │   ?   │       │
│             │ ├───────┤       │
│             │ │   ?   │       │
│             │ └───────┘       │
└─────────────┴─────────────────┘
```

### 7.2 HUD Elements

| Element | Position | Content |
|---------|----------|---------|
| Current Score | Top-left | Numeric display |
| High Score | Top-right | Numeric display |
| Level | Left sidebar | Current level number |
| Lines Cleared | Left sidebar | Cumulative line count |
| Ghost Piece | On board | Faint outline showing drop destination |
| Pause Overlay | Center | "PAUSED" indicator when paused |
| Game Over Screen | Full screen | Final score, restart option |

### 7.3 Line Clear Animations

**Animation Specifications:**
- Duration: 150-300ms per animation
- Easing: Ease-out effect
- Stages:
  1. **Highlight** (50ms): Flash cleared lines white/bright
  2. **Explosion** (100ms): Particles/fragments scatter outward
  3. **Collapse** (100ms): Rows above fall with gravity
  4. **Score Pop** (50ms): Score popup appears briefly

**Effect Options:**
- Particle burst from each cell
- Horizontal wipe effect
- Color flash transition

### 7.4 Visual Feedback

| Event | Visual Effect |
|-------|--------------|
| Line Clear | Flash + particle explosion |
| Level Up | Screen border glow (2 seconds) |
| Game Over | Fade to black overlay |
| Pause | Darken background overlay |
| Hard Drop | Brief screen shake (optional) |

---

## Game State Management

### 8.1 Game States

```
START_SCREEN → GAME_PLAY → PAUSED ↔ GAME_OVER
                      ↓
                   GAME_PLAY (unpause)
                      
GAME_OVER → START_SCREEN (new game)
```

### 8.2 State Descriptions

| State | Description | User Actions Available |
|-------|-------------|----------------------|
| START_SCREEN | Title/menu screen | Start new game, view controls |
| GAME_PLAY | Active gameplay | All movement, rotate, pause |
| PAUSED | Gameplay suspended | Resume, quit to menu |
| GAME_OVER | Session ended | Restart, view high score |

### 8.3 Game Over Conditions

**Detection Criteria:**
1. Spawn collision: New piece cannot be placed without overlapping existing blocks
2. Check performed at spawn point immediately after piece generation
3. Trigger final frame rendering with final score

**Game Over Sequence:**
1. Stop all piece movement
2. Display "GAME OVER" overlay (1 second)
3. Show final statistics:
   - Final Score
   - Highest Level Reached
   - Total Lines Cleared
   - Pieces Placed
4. Enable "New Game" button/action

---

## Acceptance Criteria

### AC-1: Core Grid System

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-1.1 | Grid must be exactly 10 columns × 20 rows | Unit test grid initialization |
| AC-1.2 | All boundary walls (left, right, bottom) are solid | Collision detection test |
| AC-1.3 | Empty cells initialize as unfilled | Grid inspection after start |

### AC-2: Tetromino Implementation

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-2.1 | All 7 tetrominoes present (I, J, L, O, S, T, Z) | Shape enumeration test |
| AC-2.2 | Each tetromino uses correct color assignment | Visual/color check |
| AC-2.3 | Each tetromino composed of exactly 4 blocks | Block count verification |
| AC-2.4 | Randomization provides equal probability for all shapes | Statistical distribution test (1000+ spawns) |

### AC-3: Movement and Rotation

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-3.1 | Pieces move left/right when directed | Manual testing |
| AC-3.2 | Pieces fall automatically based on level speed | Timer verification |
| AC-3.3 | Rotation is blocked at boundaries (no clipping) | Wall-adjacent rotation test |
| AC-3.4 | Wall kicks allow rotation where possible | Edge case rotation scenarios |
| AC-3.5 | Soft drop accelerates descent | Time measurement test |
| AC-3.6 | Hard drop instantly places piece at bottom | Distance calculation test |

### AC-4: Line Clearing

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-4.1 | Complete horizontal row triggers line clear | Place full row test |
| AC-4.2 | Multiple simultaneous lines clear together | 2-4 line clear tests |
| AC-4.3 | Lines above fall down after clear | Row position verification |
| AC-4.4 | Incomplete rows remain unchanged | Partial row test |
| AC-4.5 | Animation displays during line clear | Visual verification |

### AC-5: Scoring System

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-5.1 | Single line clears award 100 × Level points | Automated scoring test |
| AC-5.2 | Double line clears award 300 × Level points | 2-line clear test |
| AC-5.3 | Triple line clears award 500 × Level points | 3-line clear test |
| AC-5.4 | Tetris (4 lines) awards 800 × Level points | 4-line clear test |
| AC-5.5 | Soft drop adds 1 point per cell | Continuous soft drop test |
| AC-5.6 | Hard drop adds 2 points per cell fallen | Hard drop distance test |
| AC-5.7 | Score persists correctly through game session | End-to-end score tracking |

### AC-6: Level Progression

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-6.1 | Game starts at Level 1 | Startup verification |
| AC-6.2 | Level increases every 10 lines at Level 1 | Line count test |
| AC-6.3 | Subsequent levels require cumulative lines (10× level) | Multi-level progression test |
| AC-6.4 | Level indicator updates visually | HUD display test |
| AC-6.5 | Maximum level caps at 15 | Level cap test |

### AC-7: Speed Progression

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-7.1 | Drop speed increases with level | Timing measurement test |
| AC-7.2 | Level 1 drop interval ≈ 800ms | Precise timing test |
| AC-7.3 | Level 15+ drop interval ≈ 83ms | Max speed verification |
| AC-7.4 | Speed changes immediately upon level up | Transition test |

### AC-8: Game Controls

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-8.1 | All keyboard inputs respond within 50ms | Latency measurement |
| AC-8.2 | Pause toggles gameplay suspension | Pause/resume test |
| AC-8.3 | Start creates new game session | New game test |
| AC-8.4 | Quit closes application cleanly | Application exit test |

### AC-9: Next Piece Preview

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-9.1 | Next piece displayed correctly | Visual verification |
| AC-9.2 | Preview matches actual incoming piece | Prediction accuracy test (100 trials) |
| AC-9.3 | Preview positions at right side of board | Layout verification |

### AC-10: Game Over Detection

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-10.1 | Game over triggers when spawn point blocked | Flood-fill scenario test |
| AC-10.2 | Game over prevents further piece movement | Post-trigger lock verification |
| AC-10.3 | Final score displayed on game over screen | Score display test |
| AC-10.4 | Restart creates fresh game at Level 1 | Restart flow test |

### AC-11: Persistence and High Scores

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-11.1 | High score persists between sessions | Close/reopen test |
| AC-11.2 | High score updates only on improvement | Update logic test |
| AC-11.3 | Configuration saved in accessible format | File format verification |

### AC-12: Performance Requirements

| ID | Criterion | Verification Method |
|----|-----------|--------------------|
| AC-12.1 | Maintains 60 FPS during normal gameplay | Frame rate monitoring |
| AC-12.2 | No visible lag during line clear animations | Animation smoothness test |
| AC-12.3 | Memory usage stable over extended play | Long-session monitoring |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Tetromino | A geometric shape composed of 4 squares used in Tetris |
| Tetris | Clearing 4 lines simultaneously with the I-piece |
| Soft Drop | Player-initiated downward movement (slow) |
| Hard Drop | Player-initiated instant placement |
| Wall Kick | Adjusting piece position when rotation blocked by wall |
| Lock Delay | Grace period before piece becomes permanent |
| Ghost Piece | Preview showing where current piece will land |

---

## Appendix B: Testing Checklist

### Functional Tests
- [ ] Grid initialization
- [ ] All 7 shapes spawn correctly
- [ ] Rotation in center of field
- [ ] Rotation at left wall
- [ ] Rotation at right wall
- [ ] Rotation at corner
- [ ] Line clear (single)
- [ ] Line clear (double)
- [ ] Line clear (triple)
- [ ] Line clear (tetris)
- [ ] Speed increases by level
- [ ] Score calculation accuracy
- [ ] Level advancement logic
- [ ] Game over trigger
- [ ] Pause/resume functionality
- [ ] New game reset

### Integration Tests
- [ ] Full game loop completion
- [ ] High score persistence
- [ ] Configuration save/load
- [ ] Input handling under load

### Performance Tests
- [ ] 60 FPS maintenance
- [ ] Animation performance
- [ ] Memory leak check (1 hour+)

---

*Document Version 1.0 - Approved for Implementation*
