#pragma once
#include "lvgl.h"
#ifdef __cplusplus
extern "C" {
#endif
// Reuses the upstream passphrase-review space-block renderer without new fonts.
bool ss_attach_review_spaces(lv_obj_t *label,const lv_font_t *font);
#ifdef __cplusplus
}
#endif
