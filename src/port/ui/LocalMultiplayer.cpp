#include "LocalMultiplayer.h"
#include <libultraship.h>

#include <algorithm>
#include <cstdio>
#include <imgui.h>
#include <imgui_internal.h>
#include <fast/Fast3dWindow.h>
#include <fast/interpreter.h>
#include <ship/Context.h>

extern "C" {
#include "local_multiplayer.h"
#include "main.h"
#include "menus.h"
#include "code_800029B0.h"
#include "code_80005FD0.h"
}

namespace GameUI {
namespace {
constexpr ImU32 playerColors[8] = {
    IM_COL32(75, 155, 255, 255), IM_COL32(255, 185, 55, 255),
    IM_COL32(80, 220, 100, 255), IM_COL32(255, 100, 100, 255),
    IM_COL32(205, 135, 255, 255), IM_COL32(70, 230, 230, 255),
    IM_COL32(255, 125, 195, 255), IM_COL32(235, 235, 235, 255),
};
constexpr const char* characters[8] = { "Mario", "Luigi", "Yoshi", "Toad", "DK", "Wario", "Peach", "Bowser" };
constexpr const char* items[] = { "--", "Banana", "Bananas", "Green shell", "3 green shells", "Red shell",
    "3 red shells", "Blue shell", "Lightning", "Fake box", "Star", "Boo", "Mushroom", "2 mushrooms",
    "3 mushrooms", "Gold mushroom" };
}

void DrawLocalMultiplayer() {
    auto window = std::dynamic_pointer_cast<Fast::Fast3dWindow>(Ship::Context::GetRawInstance()->GetWindow());
    if (!window) return;
    auto interpreter = window->GetInterpreterWeak().lock();
    if (!interpreter) return;
    const auto& viewport = interpreter->mGameWindowViewport;
    const auto origin = ImGui::GetMainViewport()->Pos;
    const ImVec2 base(origin.x + viewport.x, origin.y + viewport.y);
    const float sx = viewport.width / 320.0f;
    const float sy = viewport.height / 240.0f;
    if (sx <= 0 || sy <= 0) return;
    auto* draw = ImGui::GetForegroundDrawList();
    auto point = [&](float x, float y) { return ImVec2(base.x + x * sx, base.y + y * sy); };
    const float fontSize = std::clamp(7.0f * sy, 12.0f, 24.0f);
    auto text = [&](float x, float y, ImU32 color, const char* value) {
        auto pos = point(x, y);
        draw->AddText(nullptr, fontSize, ImVec2(pos.x + 1, pos.y + 1), IM_COL32(0, 0, 0, 255), value);
        draw->AddText(nullptr, fontSize, pos, color, value);
    };
    char label[128];
    if (gGamestate != RACING && gMenuSelection == MAIN_MENU) {
        draw->AddRectFilled(point(18, 18), point(302, 46), IM_COL32(15, 20, 35, 235), 4);
        snprintf(label, sizeof(label), "LOCAL PLAYERS: %d   (LEFT / RIGHT to change)", gPlayerCount);
        text(24, 21, IM_COL32_WHITE, label);
        text(24, 33, IM_COL32(200, 210, 230, 255), "1-4: Original modes    5-8: Split-screen Versus");
    }
    if (gPlayerCount <= 4) return;
    if (gGamestate != RACING && gMenuSelection == CHARACTER_SELECT_MENU) {
        draw->AddRectFilled(point(5, 202), point(315, 239), IM_COL32(15, 20, 35, 235), 4);
        for (int i = 0; i < gPlayerCount; ++i) {
            int cell = gCharacterGridSelections[i] - 1;
            snprintf(label, sizeof(label), "P%d %s %s", i + 1,
                     characters[std::clamp<int>(gCharacterSelections[i], 0, 7)],
                     gCharacterGridIsSelected[i] ? "READY" : "...");
            text(10 + (i % 4) * 77, 204 + (i / 4) * 11, playerColors[i], label);
            if (cell >= 0 && cell < 8) {
                snprintf(label, sizeof(label), "P%d%s", i + 1, gCharacterGridIsSelected[i] ? " OK" : "");
                text(27 + (cell % 4) * 64, 54 + (cell / 4) * 85 + (i / 4) * 9, playerColors[i], label);
            }
        }
        text(10, 228, IM_COL32_WHITE, "Each player: A ready / B back. A again when all ready.");
    }
    if (gGamestate != RACING || gDemoMode || !CVarGetInteger("gDrawHUD", true)) return;
    for (int i = 0; i < gPlayerCountSelection1; ++i) {
        LocalPlayerViewport view = local_player_viewport(gPlayerCountSelection1, i);
        draw->AddRect(point(view.x, view.y), point(view.x + view.width, view.y + view.height),
                      playerColors[i], 0, 0, 1.5f);
        int lap = std::clamp<int>(gLapCountByPlayerId[i] + 1, 1, 3);
        int item = gPlayers[i].currentItemCopy;
        snprintf(label, sizeof(label), "P%d  #%d  %s", i + 1, gGPCurrentRaceRankByPlayerId[i] + 1,
                 gPlayers[i].lapCount >= 3 ? "FINISH" : "");
        text(view.x + 3, view.y + 2, playerColors[i], label);
        snprintf(label, sizeof(label), "Lap %d/3   %s", lap,
                 items[item >= 0 && item < (int) std::size(items) ? item : 0]);
        text(view.x + 3, view.y + view.height - 10, IM_COL32_WHITE, label);
    }
    if (gPlayerCountSelection1 % 2) {
        LocalPlayerViewport empty = local_player_viewport(gPlayerCountSelection1, gPlayerCountSelection1);
        draw->AddRectFilled(point(empty.x, empty.y), point(empty.x + empty.width, empty.y + empty.height),
                            IM_COL32(10, 14, 25, 255));
        text(empty.x + 8, empty.y + 10, IM_COL32_WHITE, "SpaghettiKart");
    }
    if (gRaceState == RACE_FINISHED && D_8015F894 == 2) {
        draw->AddRectFilled(point(70, 12), point(250, 160), IM_COL32(15, 20, 35, 240), 4);
        text(86, 18, IM_COL32_WHITE, "VERSUS RESULTS");
        for (int rank = 0; rank < gPlayerCountSelection1; ++rank) {
            for (int player = 0; player < gPlayerCountSelection1; ++player) {
                if (gGPCurrentRaceRankByPlayerId[player] != rank) continue;
                snprintf(label, sizeof(label), "%d. Player %d   %s", rank + 1, player + 1,
                         characters[gPlayers[player].characterId]);
                text(80, 35 + rank * 14, playerColors[player], label);
            }
        }
    }
}
} // namespace GameUI
