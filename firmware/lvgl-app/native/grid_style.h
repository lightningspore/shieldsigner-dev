#pragma once
#include "lvgl.h"
#include "screen_helpers.h"
#include <nlohmann/json.hpp>
#include <optional>
#include <map>
// Parse before constructing widgets so malformed config cannot leak a screen.
inline std::optional<lv_color_t> grid_focus_color(const nlohmann::json &cfg) {
 if(!cfg.contains("button_selected_color"))return std::nullopt;
 return lv_color_hex(parse_hex_color(cfg.at("button_selected_color").get<std::string>()));
}
inline std::map<lv_obj_t*,lv_color_t> grid_colors;
inline void grid_color_deleted(lv_event_t *event) {grid_colors.erase(lv_event_get_target_obj(event));}
inline lv_color_t grid_active_color(lv_obj_t *button,lv_color_t fallback) {
 auto found=grid_colors.find(button);return found==grid_colors.end()?fallback:found->second;
}
inline void apply_grid_focus_color(lv_obj_t **buttons,size_t count,std::optional<lv_color_t> color) {
 if(!color)return;
 for(size_t i=0;i<count;++i) {
  grid_colors[buttons[i]]=*color;
  lv_obj_add_event_cb(buttons[i],grid_color_deleted,LV_EVENT_DELETE,nullptr);
  for(lv_state_t state:{LV_STATE_FOCUSED,LV_STATE_FOCUS_KEY,LV_STATE_PRESSED})
   lv_obj_set_style_bg_color(buttons[i],*color,LV_PART_MAIN|state);
 }
}
