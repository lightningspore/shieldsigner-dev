#pragma once
#include "lvgl.h"
#include <algorithm>
#include <map>
#include <optional>
#include <string>
// Only NUL-bearing inputs use a shadow buffer. The widget displays an injective
// escaped representation; edits operate on real UTF-8 codepoints, not escapes.
struct nul_text_state {std::string raw;size_t cursor;};
inline std::map<lv_obj_t*,nul_text_state> nul_text_values;
inline size_t nul_prev(const std::string &s,size_t i){if(!i)return 0;--i;while(i&&(uint8_t(s[i])&0xc0)==0x80)--i;return i;}
inline size_t nul_next(const std::string &s,size_t i){if(i==s.size())return i;++i;while(i<s.size()&&(uint8_t(s[i])&0xc0)==0x80)++i;return i;}
inline std::string nul_visible(const std::string &s){std::string out;for(char c:s){if(c=='\0')out+="\\0";else if(c=='\\')out+="\\\\";else out+=c;}return out;}
inline void nul_text_deleted(lv_event_t *event){auto found=nul_text_values.find(lv_event_get_target_obj(event));if(found!=nul_text_values.end()){std::fill(found->second.raw.begin(),found->second.raw.end(),'\0');nul_text_values.erase(found);}}
inline void nul_refresh(lv_obj_t *ta,nul_text_state &state){
 auto visible=nul_visible(state.raw);auto prefix=nul_visible(state.raw.substr(0,state.cursor));
 uint32_t cursor=0;for(unsigned char c:prefix)if((c&0xc0)!=0x80)++cursor;
 lv_textarea_set_text(ta,visible.c_str());lv_textarea_set_cursor_pos(ta,cursor);
}
inline void nul_set_initial(lv_obj_t *ta,const std::string &text){
 if(text.find('\0')==std::string::npos){lv_textarea_set_text(ta,text.c_str());return;}
 auto inserted=nul_text_values.emplace(ta,nul_text_state{text,text.size()});
 lv_obj_add_event_cb(ta,nul_text_deleted,LV_EVENT_DELETE,nullptr);nul_refresh(ta,inserted.first->second);
}
inline std::string nul_result(lv_obj_t *ta){auto found=nul_text_values.find(ta);return found==nul_text_values.end()?std::string(lv_textarea_get_text(ta)):found->second.raw;}
inline void nul_delete(lv_obj_t *ta){auto found=nul_text_values.find(ta);if(found==nul_text_values.end()){lv_textarea_delete_char(ta);return;}auto &s=found->second;auto previous=nul_prev(s.raw,s.cursor);s.raw.erase(previous,s.cursor-previous);s.cursor=previous;nul_refresh(ta,s);}
inline void nul_left(lv_obj_t *ta){auto found=nul_text_values.find(ta);if(found==nul_text_values.end()){lv_textarea_cursor_left(ta);return;}auto &s=found->second;s.cursor=nul_prev(s.raw,s.cursor);nul_refresh(ta,s);}
inline void nul_right(lv_obj_t *ta){auto found=nul_text_values.find(ta);if(found==nul_text_values.end()){lv_textarea_cursor_right(ta);return;}auto &s=found->second;s.cursor=nul_next(s.raw,s.cursor);nul_refresh(ta,s);}
inline void nul_add(lv_obj_t *ta,const char *text){auto found=nul_text_values.find(ta);if(found==nul_text_values.end()){lv_textarea_add_text(ta,text);return;}auto &s=found->second;s.raw.insert(s.cursor,text);s.cursor+=std::char_traits<char>::length(text);nul_refresh(ta,s);}
