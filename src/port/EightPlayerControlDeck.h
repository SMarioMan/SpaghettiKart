#pragma once

#include <algorithm>
#include <libultraship/controller/controldevice/controller/Controller.h>
#include <ship/controller/controldeck/ControlDeck.h>
#include <ship/controller/controldevice/controller/mapping/mouse/WheelHandler.h>

// Keep the game's eight physical ports independent of N64's four-port ABI.
class EightPlayerControlDeck final : public Ship::ControlDeck {
  public:
    EightPlayerControlDeck(std::vector<CONTROLLERBUTTONS_T> extra,
                           std::shared_ptr<Ship::ControllerDefaultMappings> defaults,
                           std::unordered_map<CONTROLLERBUTTONS_T, std::string> names)
        : Ship::ControlDeck(extra, defaults, names) {
        std::vector<CONTROLLERBUTTONS_T> buttons = extra;
        for (const auto& [button, name] : names) {
            buttons.push_back(button);
        }
        for (int port = 0; port < 8; ++port) {
            mPorts.push_back(std::make_shared<Ship::ControlPort>(
                port, std::make_shared<LUS::Controller>(port, buttons)));
        }
    }

    void WriteToPad(void* buffer) override {
        auto* pads = static_cast<OSContPad*>(buffer);
        std::fill_n(pads, 8, OSContPad{});
        SDL_PumpEvents();
        Ship::WheelHandler::GetInstance()->Update();
        if (AllGameInputBlocked()) {
            return;
        }
        for (size_t port = 0; port < mPorts.size(); ++port) {
            if (auto controller = mPorts[port]->GetConnectedController()) {
                controller->ReadToPad(&pads[port]);
            }
        }
    }
};
