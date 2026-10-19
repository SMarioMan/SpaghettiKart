#include <stdio.h>
#include "local_multiplayer.h"

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "Check failed at line %d: %s\n", __LINE__, #condition); \
        return 1; \
    } \
} while (0)

int main(void) {
    for (int count = 5; count <= MAX_LOCAL_PLAYERS; count++) {
        int cells = local_multiplayer_rows(count) * 4;
        int coverage[240][320] = { 0 };
        for (int player = 0; player < cells; player++) {
            LocalPlayerViewport view = local_player_viewport(count, player);
            CHECK(view.width == 80 && view.height == 120);
            CHECK(view.x == (player % 4) * 80 && view.y == (player / 4) * 120);
            CHECK(view.x >= 0 && view.y >= 0);
            CHECK(view.x + view.width <= 320 && view.y + view.height <= 240);
            for (int y = view.y; y < view.y + view.height; y++) {
                for (int x = view.x; x < view.x + view.width; x++) {
                    CHECK(coverage[y][x]++ == 0);
                }
            }
        }
        for (int y = 0; y < 240; y++) {
            for (int x = 0; x < 320; x++) CHECK(coverage[y][x] == 1);
        }
        printf("%d players: distinct viewports cover the canvas, including unused cells\n", count);
    }
}
