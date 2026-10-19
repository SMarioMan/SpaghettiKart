#ifndef LOCAL_MULTIPLAYER_H
#define LOCAL_MULTIPLAYER_H

// Shared by viewport rendering and UI. Coordinates use the game's 320x240 canvas.
#define MAX_LOCAL_PLAYERS 8

typedef struct {
    int x, y, width, height;
} LocalPlayerViewport;

static inline int local_multiplayer_rows(int count) {
    (void) count;
    return 2;
}

static inline LocalPlayerViewport local_player_viewport(int count, int player) {
    int rows = local_multiplayer_rows(count);
    int row = player / 4;
    int top = row * 240 / rows;
    int bottom = (row + 1) * 240 / rows;
    LocalPlayerViewport view = { (player % 4) * 80, top, 80, bottom - top };
    return view;
}
#endif
