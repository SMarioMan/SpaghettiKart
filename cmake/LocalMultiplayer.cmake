# Adapt the pinned input editor to our eight-port deck without modifying the submodule.
# Fail loudly if an upstream update removes the exact four-port assumptions.
function(local_multiplayer_source source_file old_text new_text)
  set(original "${CMAKE_SOURCE_DIR}/libultraship/src/${source_file}")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${original}")
  file(READ "${original}" source)
  string(FIND "${source}" "${old_text}" position)
  if(position EQUAL -1)
    message(FATAL_ERROR "Recheck eight-player adaptation for ${source_file}")
  endif()
  string(REPLACE "${old_text}" "${new_text}" source "${source}")
  set(output "${CMAKE_BINARY_DIR}/local-multiplayer/${source_file}")
  get_filename_component(output_dir "${output}" DIRECTORY)
  file(MAKE_DIRECTORY "${output_dir}")
  set(temporary "${output}.tmp")
  file(WRITE "${temporary}" "${source}")
  configure_file("${temporary}" "${output}" COPYONLY)
  file(REMOVE "${temporary}")
  get_target_property(sources libultraship SOURCES)
  list(REMOVE_ITEM sources "${original}")
  set_property(TARGET libultraship PROPERTY SOURCES "${sources}")
  target_sources(libultraship PRIVATE "${output}")
endfunction()

local_multiplayer_source("libultraship/window/gui/InputEditorWindow.cpp"
  "for (uint8_t i = 0; i < 4; i++)" "for (uint8_t i = 0; i < 8; i++)")
local_multiplayer_source("ship/controller/physicaldevice/ConnectedPhysicalDeviceManager.cpp"
  "for (uint8_t port = 1; port < 4; port++)" "for (uint8_t port = 1; port < 8; port++)")
