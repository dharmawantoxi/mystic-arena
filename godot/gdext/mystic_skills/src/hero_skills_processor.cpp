#include "hero_skills_processor.h"

#include <godot_cpp/classes/node2d.hpp>
#include <godot_cpp/variant/utility_functions.hpp>
#include <godot_cpp/core/math.hpp>
#include <cmath>

using namespace godot;

// helpers for property access
Vector2 MysticHeroSkills::get_global_pos(Object* obj) { Variant v = obj->get("global_position"); if (v.get_type()==Variant::VECTOR2) return v; return Vector2(); }
double MysticHeroSkills::get_global_pos_x(Object* obj) { return get_global_pos(obj).x; }
double MysticHeroSkills::get_global_pos_y(Object* obj) { return get_global_pos(obj).y; }
void MysticHeroSkills::set_global_pos(Object* obj, Vector2 pos) { obj->set("global_position", pos); }
void MysticHeroSkills::set_global_pos_x(Object* obj, double x) { Vector2 p = get_global_pos(obj); p.x = x; set_global_pos(obj, p); }
void MysticHeroSkills::set_global_pos_y(Object* obj, double y) { Vector2 p = get_global_pos(obj); p.y = y; set_global_pos(obj, p); }
double MysticHeroSkills::get_hp(Object* obj) { Variant v = obj->get("hp"); return (double)v; }
double MysticHeroSkills::get_max_hp(Object* obj) { Variant v = obj->get("max_hp"); return (double)v; }
void MysticHeroSkills::set_hp(Object* obj, double v) { obj->set("hp", v); }
void MysticHeroSkills::set_max_hp(Object* obj, double v) { obj->set("max_hp", v); }
double MysticHeroSkills::get_damage(Object* obj) { Variant v = obj->get("damage"); return (double)v; }
void MysticHeroSkills::set_damage(Object* obj, double v) { obj->set("damage", (double)v); }
String MysticHeroSkills::get_team(Object* obj) { Variant v = obj->get("team"); return v; }
String MysticHeroSkills::get_hero_type(Object* obj) { Variant v = obj->get("hero_type"); return v; }
String MysticHeroSkills::get_dmg_school(Object* obj) { Variant v = obj->get("dmg_school"); return v; }
int MysticHeroSkills::get_facing(Object* obj) { Variant v = obj->get("facing"); return (int)v; }
void MysticHeroSkills::set_facing(Object* obj, int v) { obj->set("facing", v); }
int MysticHeroSkills::get_level(Object* obj) { Variant v = obj->get("level"); return (int)v; }
void MysticHeroSkills::set_level(Object* obj, int v) { obj->set("level", v); }
double MysticHeroSkills::get_base_damage(Object* obj) { Variant v = obj->get("base_damage"); return (double)v; }
void MysticHeroSkills::set_base_damage(Object* obj, double v) { obj->set("base_damage", v); }
double MysticHeroSkills::get_skill_range(Object* obj) { Variant v = obj->get("skill_range"); return (double)v; }
double MysticHeroSkills::get_attack_range(Object* obj) { Variant v = obj->get("attack_range"); return (double)v; }
Dictionary MysticHeroSkills::get_skill_data(Object* obj) { Variant v = obj->get("skill_data"); if (v.get_type()==Variant::DICTIONARY) return v; return Dictionary(); }
Variant MysticHeroSkills::get_active_skill(Object* obj) { return obj->get("active_skill"); }
void MysticHeroSkills::set_active_skill(Object* obj, Variant v) { obj->set("active_skill", v); }
int MysticHeroSkills::get_active_skill_timer(Object* obj) { Variant v = obj->get("active_skill_timer"); return (int)v; }
void MysticHeroSkills::set_active_skill_timer(Object* obj, int v) { obj->set("active_skill_timer", v); }
int MysticHeroSkills::get_skill_timer(Object* obj) { Variant v = obj->get("skill_timer"); return (int)v; }
void MysticHeroSkills::set_skill_timer(Object* obj, int v) { obj->set("skill_timer", v); }
int MysticHeroSkills::get_w_cooldown(Object* obj) { Variant v = obj->get("w_cooldown"); return (int)v; }
void MysticHeroSkills::set_w_cooldown(Object* obj, int v) { obj->set("w_cooldown", v); }
int MysticHeroSkills::get_e_cooldown(Object* obj) { Variant v = obj->get("e_cooldown"); return (int)v; }
void MysticHeroSkills::set_e_cooldown(Object* obj, int v) { obj->set("e_cooldown", v); }
int MysticHeroSkills::get_r_cooldown(Object* obj) { Variant v = obj->get("r_cooldown"); return (int)v; }
void MysticHeroSkills::set_r_cooldown(Object* obj, int v) { obj->set("r_cooldown", v); }
int MysticHeroSkills::get_skill_cooldown_max(Object* obj) { Variant v = obj->get("skill_cooldown_max"); return (int)v; }
int MysticHeroSkills::get_w_cooldown_max(Object* obj) { Variant v = obj->get("w_cooldown_max"); return (int)v; }
int MysticHeroSkills::get_e_cooldown_max(Object* obj) { Variant v = obj->get("e_cooldown_max"); return (int)v; }
int MysticHeroSkills::get_r_cooldown_max(Object* obj) { Variant v = obj->get("r_cooldown_max"); return (int)v; }
double MysticHeroSkills::get_speed_frames(Object* obj) { Variant v = obj->get("move_speed"); return (double)v / 60.0; }
void MysticHeroSkills::set_speed_frames(Object* obj, double v) { obj->set("move_speed", (double)v * 60.0); }
// GDScript membaca int(roundf(float(h.attack_cooldown) * 60.0)) -> frame bulat.
double MysticHeroSkills::get_attack_cooldown_frames(Object* obj) { Variant v = obj->get("attack_cooldown"); return (double)(int64_t)round((double)v * 60.0); }
void MysticHeroSkills::set_attack_cooldown_frames(Object* obj, double v) { obj->set("attack_cooldown", (double)v / 60.0); }
// Assign langsung `X.attack_timer = N` (frame) -> detik apa adanya; Hero.kit_lock memakai maxf().
void MysticHeroSkills::set_atk_timer_frames(Object* h, Object* target, double frames) { if (!target) { return; } if (!kit_has_atk_timer(h, target)) { return; } target->set("attack_timer", frames / 60.0); }
bool MysticHeroSkills::is_alive(Object* obj) { Variant v = obj->get("is_dead"); bool dead = (bool)v; return !dead; }
Dictionary MysticHeroSkills::get_kit(Object* obj) { Variant v = obj->get("kit"); if (v.get_type()==Variant::DICTIONARY) return v; return Dictionary(); }
void MysticHeroSkills::set_kit(Object* obj, const Dictionary& d) { obj->set("kit", d); }
Variant MysticHeroSkills::get_kit_value(Object* obj, const String& key, Variant def) { Dictionary d = get_kit(obj); if (d.has(key)) return d[key]; return def; }
void MysticHeroSkills::set_kit_value(Object* obj, const String& key, Variant value) { Dictionary d = get_kit(obj); d[key]=value; set_kit(obj, d); }
Object* MysticHeroSkills::get_target(Object* obj) { Variant v = obj->get("target"); if (v.get_type()==Variant::OBJECT) return Object::cast_to<Object>(v); return nullptr; }
void MysticHeroSkills::set_target(Object* obj, Variant v) { obj->set("target", v); }
bool MysticHeroSkills::truthy(Variant v) { if (v.get_type()==Variant::NIL) return false; if (v.get_type()==Variant::BOOL) return (bool)v; if (v.get_type()==Variant::INT) return (int64_t)v !=0; if (v.get_type()==Variant::FLOAT) return (double)v !=0.0; if (v.get_type()==Variant::STRING) { String s=v; return s.length()>0; } if (v.get_type()==Variant::ARRAY) { Array a=v; return a.size()>0; } if (v.get_type()==Variant::DICTIONARY) { Dictionary d=v; return d.size()>0; } return true; }
Variant MysticHeroSkills::py_or(Variant a, Variant b) { return truthy(a) ? a : b; }
Array MysticHeroSkills::range_array(int n) { Array a; for(int i=0;i<n;++i) a.append(i); return a; }
Dictionary MysticHeroSkills::make_dict() { return Dictionary(); }
Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1) { Dictionary d; d[k1]=v1; return d; }
Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2) { Dictionary d; d[k1]=v1; d[k2]=v2; return d; }
Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3) { Dictionary d; d[k1]=v1; d[k2]=v2; d[k3]=v3; return d; }
Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3, Variant k4, Variant v4) { Dictionary d; d[k1]=v1; d[k2]=v2; d[k3]=v3; d[k4]=v4; return d; }
bool MysticHeroSkills::in_array(const Array& arr, Variant v) { for(int i=0;i<arr.size();++i) if (arr[i]==v) return true; return false; }
Array MysticHeroSkills::make_array() { return Array(); }
Array MysticHeroSkills::make_array(Variant a) { Array arr; arr.append(a); return arr; }
Array MysticHeroSkills::make_array(Variant a, Variant b) { Array arr; arr.append(a); arr.append(b); return arr; }
Array MysticHeroSkills::make_array(Variant a, Variant b, Variant c) { Array arr; arr.append(a); arr.append(b); arr.append(c); return arr; }
Array MysticHeroSkills::make_array(Variant a, Variant b, Variant c, Variant d) { Array arr; arr.append(a); arr.append(b); arr.append(c); arr.append(d); return arr; }

// BaseSkill helpers - mirror GDScript header
double MysticHeroSkills::skill_range(Object* h, double fallback) {
    double rng = get_skill_range(h);
    if (rng==0.0) { Dictionary data = get_skill_data(h); Variant v = data.get("skill_range", fallback); rng = (double)v; if (rng==0.0) rng=fallback; }
    double ar = get_attack_range(h);
    return MAX(ar, rng);
}

Array MysticHeroSkills::kit_enemies(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant ret = h->call("kit_enemies", all_units, all_towers, all_bases);
    if (ret.get_type()==Variant::ARRAY) return ret; return Array();
}
int MysticHeroSkills::kit_skill_damage(Object* h) { Variant ret = h->call("kit_skill_damage"); return (int)ret; }
Dictionary MysticHeroSkills::kit_catalog_all(Object* h) { Variant ret = h->call("kit_catalog_all"); if (ret.get_type()==Variant::DICTIONARY) return ret; return Dictionary(); }
Dictionary MysticHeroSkills::kit_hero_levels(Object* h) { Variant ret = h->call("kit_hero_levels"); if (ret.get_type()==Variant::DICTIONARY) return ret; return Dictionary(); }
void MysticHeroSkills::kit_hit(Object* h, Object* target, int dmg, const String& team, Variant src, const String& school) { if (!target) return; h->call("kit_hit", target, dmg, team, src, school); }
void MysticHeroSkills::kit_slow(Object* h, Object* target, double amount, double dur_frames) { if (!target) return; h->call("kit_slow", target, amount, dur_frames); }
void MysticHeroSkills::kit_lock(Object* h, Object* target, double frames) { if (!target) return; h->call("kit_lock", target, frames); }
double MysticHeroSkills::kit_atk_timer(Object* h, Object* target) { if (!target) return 0; Variant ret = h->call("kit_atk_timer", target); return (double)ret; }
bool MysticHeroSkills::kit_unit_alive(Object* h, Object* target) { if (!target) return false; Variant ret = h->call("kit_unit_alive", target); return (bool)ret; }
bool MysticHeroSkills::kit_has_slow(Object* h, Object* target) { if (!target) return false; Variant ret = h->call("kit_has_slow", target); return (bool)ret; }
bool MysticHeroSkills::kit_has_atk_timer(Object* h, Object* target) { if (!target) return false; Variant ret = h->call("kit_has_atk_timer", target); return (bool)ret; }
bool MysticHeroSkills::kit_has_hp(Object* h, Object* target) { if (!target) return false; Variant ret = h->call("kit_has_hp", target); return (bool)ret; }
void MysticHeroSkills::kit_shake(Object* h, double amount) { h->call("kit_shake", amount); }
void MysticHeroSkills::kit_sound(Object* h, double volume) { h->call("kit_sound", volume); }
void MysticHeroSkills::kit_popup(Object* h, const String& text, bool critical) { h->call("kit_popup", text, critical); }
void MysticHeroSkills::kit_skill_proj(Object* h, Object* target, double speed) { if (!target) return; h->call("kit_skill_proj", target, speed); }
void MysticHeroSkills::kit_fx_cast(Object* h, const String& skill) { h->call("kit_fx_cast", skill); }
void MysticHeroSkills::kit_fx_impact(Object* h, double x, double y, double r, const String& skill) { h->call("kit_fx_impact", x, y, r, skill); }

Array MysticHeroSkills::enemies_in_range(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, Variant center_x, Variant center_y) {
    double cx = center_x.get_type()==Variant::NIL ? get_global_pos_x(h) : (double)center_x;
    double cy = center_y.get_type()==Variant::NIL ? get_global_pos_y(h) : (double)center_y;
    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);
    Array in_range;
    for (int i=0;i<enemies.size();++i) {
        Variant vv = enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e = Object::cast_to<Object>(vv); if (!e) continue;
        double dx = get_global_pos_x(e) - cx; double dy = get_global_pos_y(e) - cy; double dist = Vector2(dx, dy).length();
        if (dist <= range_val) { Array pair; pair.append(e); pair.append(dist); in_range.append(pair); }
    }
    return in_range;
}
int MysticHeroSkills::deal_aoe(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, double damage_multiplier) {
    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);
    int hit_count=0;
    for (int i=0;i<enemies.size();++i) { Variant vv=enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if (!e) continue;
        double dx = get_global_pos_x(e) - get_global_pos_x(h); double dy = get_global_pos_y(e) - get_global_pos_y(h); double dist = Vector2(dx,dy).length();
        if (dist <= range_val) { int dmg = (int)((double)kit_skill_damage(h) * damage_multiplier); kit_hit(h, e, dmg, get_team(h), h, get_dmg_school(h)); ++hit_count; }
    }
    return hit_count;
}
Object* MysticHeroSkills::acquire_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val) {
    double rng = range_val.get_type()==Variant::NIL ? skill_range(h) : (double)range_val;
    double reach = rng * 1.15;
    Object* cur = get_target(h);
    if (cur && kit_unit_alive(h, cur)) { double dx = get_global_pos_x(cur) - get_global_pos_x(h); double dy = get_global_pos_y(cur) - get_global_pos_y(h); if (Vector2(dx,dy).length() <= reach) return cur; }
    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);
    Object* best=nullptr; double best_dist=reach;
    for (int i=0;i<enemies.size();++i) { Variant vv=enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if (!e) continue; if (!kit_unit_alive(h,e)) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); double d=Vector2(dx,dy).length(); if (d<=best_dist) { best=e; best_dist=d; } }
    if (best) set_target(h, best);
    return best;
}
bool MysticHeroSkills::has_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val) {
    return acquire_target(h, all_units, all_towers, all_bases, range_val)!=nullptr;
}
int MysticHeroSkills::default_visual_duration(const String& key) {
    if (key=="q") return 60; if (key=="w") return 90; if (key=="e") return 60; if (key=="r") return 100; return 60;
}
bool MysticHeroSkills::is_starter_kind(const String& hero_type) {
    return hero_type=="grimjaw" || hero_type=="kaizen" || hero_type=="sylara" || hero_type=="thorne" || hero_type=="vex" || hero_type=="zephyr";
}
int MysticHeroSkills::visual_duration_kind(const String& kind, const String& hero_type, const String& key) {
    if (kind=="boss") {
        if (hero_type=="nyzrak") { if (key=="q") return 50; if (key=="w") return 50; if (key=="e") return 70; if (key=="r") return 90; }
        if (hero_type=="vhalzun") { if (key=="q") return 60; if (key=="w") return 80; if (key=="e") return 60; if (key=="r") return 100; }
        return default_visual_duration(key);
    }
    if (kind=="grimjaw") { if (key=="q") return 180; if (key=="w") return 90; if (key=="e") return 60; if (key=="r") return 90; }
    if (kind=="kaizen") { if (key=="q") return 60; if (key=="w") return 90; if (key=="e") return 60; if (key=="r") return 100; }
    if (kind=="sylara") { if (key=="q") return 180; if (key=="w") return 180; if (key=="e") return 150; if (key=="r") return 60; }
    if (kind=="thorne") { if (key=="q") return 40; if (key=="w") return 100; if (key=="e") return 60; if (key=="r") return 120; }
    if (kind=="vex") { if (key=="q") return 40; if (key=="w") return 100; if (key=="e") return 60; if (key=="r") return 80; }
    if (kind=="zephyr") { if (key=="q") return 240; if (key=="w") return 180; if (key=="e") return 180; if (key=="r") return 240; }
    return default_visual_duration(key);
}
int MysticHeroSkills::visual_duration(const String& hero_type, const String& key) {
    // API tanpa kind (dipakai HeroSkillKitLoader.get_visual_duration):
    // kind diturunkan dari hero_type — 6 starter punya kelas handler
    // sendiri, sisanya lewat BossHeroSkills (kind "boss").
    return visual_duration_kind(is_starter_kind(hero_type) ? hero_type : String("boss"), hero_type, key);
}
void MysticHeroSkills::set_active_skill(Object* h, const String& kind, const String& key, Variant duration) {
    int dur = duration.get_type()==Variant::NIL ? visual_duration_kind(kind, get_hero_type(h), key) : (int)duration;
    set_active_skill(h, Variant(key)); set_active_skill_timer(h, dur);
}
void MysticHeroSkills::trigger_q(Object* h, const String& kind, double shake_amount, Variant visual_duration) {
    set_skill_timer(h, get_skill_cooldown_max(h)); set_active_skill(h, kind, "q", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.7);
}
void MysticHeroSkills::trigger_w(Object* h, const String& kind, double shake_amount, Variant visual_duration) {
    set_w_cooldown(h, get_w_cooldown_max(h)); set_active_skill(h, kind, "w", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.6);
}
void MysticHeroSkills::trigger_e(Object* h, const String& kind, double shake_amount, Variant visual_duration) {
    set_e_cooldown(h, get_e_cooldown_max(h)); set_active_skill(h, kind, "e", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.7);
}
void MysticHeroSkills::trigger_r(Object* h, const String& kind, double shake_amount, Variant visual_duration) {
    set_r_cooldown(h, get_r_cooldown_max(h)); set_active_skill(h, kind, "r", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 1.0);
}

String MysticHeroSkills::hero_kind(Object* h) {
    String ht = get_hero_type(h);
    if (ht=="grimjaw" || ht=="kaizen" || ht=="sylara" || ht=="thorne" || ht=="vex" || ht=="zephyr") return ht;
    return "boss";
}

// BossHeroSkills.init_state L345
void MysticHeroSkills::bosshero_init_state(Object* h) {
    set_active_skill(h, Variant());
    set_active_skill_timer(h, 0);
    set_kit_value(h, "flux_target", Variant());
    set_kit_value(h, "flux_active_timer", 0);
    set_kit_value(h, "vortex_x", 0);
    set_kit_value(h, "vortex_y", 0);
    set_kit_value(h, "vortex_active_timer", 0);
    set_kit_value(h, "mana_void_x", 0);
    set_kit_value(h, "mana_void_y", 0);
    set_kit_value(h, "blink_from_x", 0);
    set_kit_value(h, "blink_from_y", 0);
    set_kit_value(h, "rage_active", false);
    set_kit_value(h, "rage_timer", 0);
    set_kit_value(h, "defense_boost", false);
    set_kit_value(h, "defense_timer", 0);
    set_kit_value(h, "clones_active_timer", 0);
    set_kit_value(h, "clones_positions", Array());
    set_kit_value(h, "w_target_x", 0);
    set_kit_value(h, "w_target_y", 0);
    set_kit_value(h, "w_dir_x", 1);
    set_kit_value(h, "w_dir_y", 0);
    set_kit_value(h, "r_dir_x", 1);
    set_kit_value(h, "r_dir_y", 0);
    set_kit_value(h, "cold_feet_target_x", 0);
    set_kit_value(h, "cold_feet_target_y", 0);
    set_kit_value(h, "dragon_form_active", false);
    set_kit_value(h, "dragon_form_timer", 0);
    set_kit_value(h, "dragon_blood_active", false);
    set_kit_value(h, "dragon_blood_timer", 0);
}

// BossHeroSkills.update_timers L383
void MysticHeroSkills::bosshero_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant clone_damage;
    Variant dist;
    Variant e;
    Variant enemies;
    Variant stats;

    if (get_kit_value(h, "rage_active")) {
        set_kit_value(h, "rage_timer", (int)get_kit_value(h, "rage_timer") - (int)(1));
        if (((double)(get_kit_value(h, "rage_timer")) <= 0)) {
            set_kit_value(h, "rage_active", false);
            stats = kit_catalog_all(h)[get_hero_type(h)];
            set_damage(h, ((Dictionary)(stats))["damage"]);
        }
    }
    if (get_kit_value(h, "defense_boost")) {
        set_kit_value(h, "defense_timer", (int)get_kit_value(h, "defense_timer") - (int)(1));
        if (((double)(get_kit_value(h, "defense_timer")) <= 0)) {
            set_kit_value(h, "defense_boost", false);
        }
    }
    if (((double)(get_kit_value(h, "vortex_active_timer")) > 0)) {
        set_kit_value(h, "vortex_active_timer", (int)get_kit_value(h, "vortex_active_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "vortex_active_timer")), (double)(20))) == 0)) {
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_kit_value(h, "vortex_x"))), ((double)(get_global_pos_y(e)) - (double)(get_kit_value(h, "vortex_y")))).length();
                if (((double)(dist) <= 80)) {
                    kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.3))), get_team(h), Variant(), "");
                    if (kit_has_slow(h, e)) {
                        kit_slow(h, e, 0.5, 60);
                    }
                }
            }
        }
    }
    if (((double)(get_kit_value(h, "flux_active_timer")) > 0)) {
        set_kit_value(h, "flux_active_timer", (int)get_kit_value(h, "flux_active_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "flux_active_timer")), (double)(30))) == 0)) {
            if ((get_kit_value(h, "flux_target")) && (kit_unit_alive(h, get_kit_value(h, "flux_target")))) {
                kit_hit(h, get_kit_value(h, "flux_target"), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.3))), get_team(h), Variant(), "");
                if (kit_has_slow(h, get_kit_value(h, "flux_target"))) {
                    kit_slow(h, get_kit_value(h, "flux_target"), 0.4, 60);
                }
            }
        }
    }
    if (((double)(get_kit_value(h, "clones_active_timer")) > 0)) {
        set_kit_value(h, "clones_active_timer", (int)get_kit_value(h, "clones_active_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "clones_active_timer")), (double)(40))) == 0)) {
            if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
                clone_damage = (int64_t)(((double)(get_damage(h)) * 0.5));
                kit_hit(h, get_target(h), (int)(clone_damage), get_team(h), Variant(), "");
            }
        }
    }
    if (get_kit_value(h, "dragon_form_active", false)) {
        set_kit_value(h, "dragon_form_timer", (int)get_kit_value(h, "dragon_form_timer") - (int)(1));
        if (((double)(get_kit_value(h, "dragon_form_timer")) <= 0)) {
            set_kit_value(h, "dragon_form_active", false);
            stats = kit_catalog_all(h)[get_hero_type(h)];
            set_damage(h, ((Dictionary)(stats))["damage"]);
        }
    }
    if (get_kit_value(h, "dragon_blood_active", false)) {
        set_kit_value(h, "dragon_blood_timer", (int)get_kit_value(h, "dragon_blood_timer") - (int)(1));
        if (((double)(get_kit_value(h, "dragon_blood_timer")) <= 0)) {
            set_kit_value(h, "dragon_blood_active", false);
        }
    }
}

// BossHeroSkills._cast_q_mana_break L1031
void MysticHeroSkills::bosshero_cast_q_mana_break(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_blink L1038
void MysticHeroSkills::bosshero_cast_w_blink(Object* h) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant offset;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 25);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_kit_value(h, "blink_from_x", get_global_pos_x(h));
        set_kit_value(h, "blink_from_y", get_global_pos_y(h));
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > 0)) {
            offset = MAX((double)(0), (double)(((double)(dist) - 60)));
            set_global_pos_x(h, ((double)(get_global_pos_x(h)) + (double)(((double)(((double)(dx) / (double)(dist))) * (double)(offset)))));
            set_global_pos_y(h, ((double)(get_global_pos_y(h)) + (double)(((double)(((double)(dy) / (double)(dist))) * (double)(offset)))));
        }
    }
}

// BossHeroSkills._cast_e_counterspell L1052
void MysticHeroSkills::bosshero_cast_e_counterspell(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_r_mana_void L1062
void MysticHeroSkills::bosshero_cast_r_mana_void(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    set_kit_value(h, "mana_void_x", get_global_pos_x(h));
    set_kit_value(h, "mana_void_y", get_global_pos_y(h));
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_kit_value(h, "mana_void_x"))), ((double)(get_global_pos_y(e)) - (double)(get_kit_value(h, "mana_void_y")))).length();
        if (((double)(dist) <= 180)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_q_spark_wraith L1078
void MysticHeroSkills::bosshero_cast_q_spark_wraith(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_flux L1085
void MysticHeroSkills::bosshero_cast_w_flux(Object* h) {
    set_active_skill(h, "w");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_kit_value(h, "flux_target", get_target(h));
        set_kit_value(h, "flux_active_timer", 240);
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.5))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.5, 240);
        }
    }
}

// BossHeroSkills._cast_e_magnetic_field L1096
void MysticHeroSkills::bosshero_cast_e_magnetic_field(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 90)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.7))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(45)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.08));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_tempest_double L1108
void MysticHeroSkills::bosshero_cast_r_tempest_double(Object* h) {
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 60);
    set_kit_value(h, "clones_active_timer", 480);
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_battle_hunger L1119
void MysticHeroSkills::bosshero_cast_q_battle_hunger(Object* h) {
    Variant base_damage;
    Variant heal;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 90);
    set_kit_value(h, "rage_active", true);
    set_kit_value(h, "rage_timer", 300);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.5)));
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_w_counter_helix L1133
void MysticHeroSkills::bosshero_cast_w_counter_helix(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_berserkers_call L1142
void MysticHeroSkills::bosshero_cast_e_berserkers_call(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    set_kit_value(h, "defense_boost", true);
    set_kit_value(h, "defense_timer", 180);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(30)));
            }
        }
    }
}

// BossHeroSkills._cast_r_culling_blade L1155
void MysticHeroSkills::bosshero_cast_r_culling_blade(Object* h) {
    Variant damage;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 60);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        damage = (int64_t)(((double)(kit_skill_damage(h)) * 2.5));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(get_max_hp(get_target(h))))) < 0.3)) {
            damage = (int64_t)(((double)(damage) * 2));
        }
        kit_hit(h, get_target(h), (int)(damage), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_q_mist_coil L1169
void MysticHeroSkills::bosshero_cast_q_mist_coil(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 30);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aphotic_shield L1176
void MysticHeroSkills::bosshero_cast_w_aphotic_shield(Object* h, const Array& enemies) {
    Variant e;
    Variant shield_hp;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
    shield_hp = (int64_t)(((double)(get_max_hp(h)) * 0.25));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(shield_hp)))));
}

// BossHeroSkills._cast_e_darkness_gale L1185
void MysticHeroSkills::bosshero_cast_e_darkness_gale(Object* h) {
    Variant dist;
    Variant dx;
    Variant dy;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > 0)) {
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(dist))) * 80)));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(dist))) * 80)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_r_death_sever L1198
void MysticHeroSkills::bosshero_cast_r_death_sever(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 180)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.5))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_q_acid_spray L1209
void MysticHeroSkills::bosshero_cast_q_acid_spray(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_unstable_concoction L1216
void MysticHeroSkills::bosshero_cast_w_unstable_concoction(Object* h, const Array& enemies) {
    Variant e;
    Variant target_x;
    Variant target_y;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 60);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        target_x = get_global_pos_x(get_target(h));
        target_y = get_global_pos_y(get_target(h));
    } else {
        target_x = get_global_pos_x(h);
        target_y = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(target_x)), ((double)(get_global_pos_y(e)) - (double)(target_y))).length()) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 180);
            }
        }
    }
    set_kit_value(h, "w_target_x", target_x);
    set_kit_value(h, "w_target_y", target_y);
}

// BossHeroSkills._cast_e_chemical_rage L1236
void MysticHeroSkills::bosshero_cast_e_chemical_rage(Object* h) {
    Variant base_damage;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    set_kit_value(h, "rage_active", true);
    set_kit_value(h, "rage_timer", 360);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.5)));
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_greevils_greed L1249
void MysticHeroSkills::bosshero_cast_r_greevils_greed(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;
    Variant kills;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    kills = 0;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.5))), get_team(h), Variant(), "");
            if (!(kit_unit_alive(h, e))) {
                kills = (double)(kills) + (double)(1);
            }
        }
    }
    if (((double)(kills) > 0)) {
        heal = ((double)(kills) * 100);
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
    }
}

// BossHeroSkills._cast_q_ice_vortex L1267
void MysticHeroSkills::bosshero_cast_q_ice_vortex(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 60);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_kit_value(h, "vortex_x", get_global_pos_x(get_target(h)));
        set_kit_value(h, "vortex_y", get_global_pos_y(get_target(h)));
    } else {
        set_kit_value(h, "vortex_x", ((double)(get_global_pos_x(h)) + 100));
        set_kit_value(h, "vortex_y", get_global_pos_y(h));
    }
    set_kit_value(h, "vortex_active_timer", 180);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_kit_value(h, "vortex_x"))), ((double)(get_global_pos_y(e)) - (double)(get_kit_value(h, "vortex_y")))).length();
        if (((double)(dist) <= 80)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.6))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_w_chilling_touch L1285
void MysticHeroSkills::bosshero_cast_w_chilling_touch(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant line_width;
    Variant max_range;
    Variant perp;
    Variant proj;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    max_range = 400;
    line_width = 30;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < (double)(max_range))) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < (double)(line_width))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
                if (kit_has_slow(h, e)) {
                    kit_slow(h, e, 0.6, 180);
                }
            }
        }
    }
    set_kit_value(h, "w_dir_x", dx);
    set_kit_value(h, "w_dir_y", dy);
}

// BossHeroSkills._cast_e_ice_blast L1319
void MysticHeroSkills::bosshero_cast_e_ice_blast(Object* h) {
    set_active_skill(h, "e");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.5))), get_team(h), Variant(), "");
        if (kit_has_atk_timer(h, get_target(h))) {
            kit_lock(h, get_target(h), MAX((double)(kit_atk_timer(h, get_target(h))), (double)(90)));
        }
    }
}

// BossHeroSkills._cast_r_cold_feet L1329
void MysticHeroSkills::bosshero_cast_r_cold_feet(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant line_width;
    Variant max_range;
    Variant perp;
    Variant proj;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    max_range = 500;
    line_width = 60;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < (double)(max_range))) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < (double)(line_width))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 3.0))), get_team(h), Variant(), "");
                if (kit_has_slow(h, e)) {
                    kit_slow(h, e, 0.7, 240);
                }
            }
        }
    }
    set_kit_value(h, "r_dir_x", dx);
    set_kit_value(h, "r_dir_y", dy);
}

// BossHeroSkills._cast_q_arctic_burn L1370
void MysticHeroSkills::bosshero_cast_q_arctic_burn(Object* h, const Array& enemies) {
    Variant e;
    Variant ex;
    Variant ey;
    Variant line_width;
    Variant ln;
    Variant max_range;
    Variant proj;
    Variant sx;
    Variant sy;
    Variant tx;
    Variant ty;
    Variant ux;
    Variant uy;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = get_global_pos_x(h);
        ty = get_global_pos_y(h);
    }
    sx = get_global_pos_x(h);
    sy = get_global_pos_y(h);
    max_range = 240.0;
    line_width = 26.0;
    ln = py_or(Vector2(((double)(tx) - (double)(sx)), ((double)(ty) - (double)(sy))).length(), 1.0);
    ux = ((double)(((double)(tx) - (double)(sx))) / (double)(ln));
    uy = ((double)(((double)(ty) - (double)(sy))) / (double)(ln));
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(sx));
        ey = ((double)(get_global_pos_y(e)) - (double)(sy));
        proj = ((double)(((double)(ex) * (double)(ux))) + (double)(((double)(ey) * (double)(uy))));
        if ((0 < (double)(proj)) && ((double)(proj) < (double)(max_range))) {
            if (((double)(Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(uy))))) + (double)(((double)(ey) * (double)(ux))))))) < (double)(line_width))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
                if (kit_has_slow(h, e)) {
                    kit_slow(h, e, 0.4, 120);
                }
            }
        }
    }
    kit_fx_impact(h, tx, ty, 60, "q");
}

// BossHeroSkills._cast_w_splinter_blast L1396
void MysticHeroSkills::bosshero_cast_w_splinter_blast(Object* h, const Array& enemies) {
    Variant e;
    Variant tx;
    Variant ty;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = get_global_pos_x(h);
        ty = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 80)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.3, 60);
            }
        }
    }
    kit_fx_impact(h, tx, ty, 80, "w");
}

// BossHeroSkills._cast_e_winters_curse L1415
void MysticHeroSkills::bosshero_cast_e_winters_curse(Object* h, const Array& enemies) {
    set_active_skill(h, "e");
    set_active_skill_timer(h, 70);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        if (kit_has_atk_timer(h, get_target(h))) {
            kit_lock(h, get_target(h), MAX((double)(kit_atk_timer(h, get_target(h))), (double)(90)));
        }
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.7, 180);
        }
        kit_fx_impact(h, get_global_pos_x(get_target(h)), get_global_pos_y(get_target(h)), 44, "e");
    }
}

// BossHeroSkills._cast_r_cold_embrace L1434
void MysticHeroSkills::bosshero_cast_r_cold_embrace(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    set_kit_value(h, "shield_active", true);
    set_kit_value(h, "shield_timer", 240);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 180);
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 200, "r");
}

// BossHeroSkills._cast_q_dragon_breath L1457
void MysticHeroSkills::bosshero_cast_q_dragon_breath(Object* h, const Array& enemies) {
    Variant allowed_width;
    Variant cone_width;
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant max_range;
    Variant perp;
    Variant proj;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    max_range = 250;
    cone_width = 60;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < (double)(max_range))) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            allowed_width = ((double)(cone_width) * (double)((0.3 + (double)(((double)(((double)(proj) / (double)(max_range))) * 0.7)))));
            if (((double)(perp) < (double)(allowed_width))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.6))), get_team(h), Variant(), "");
                if (kit_has_atk_timer(h, e)) {
                    kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(45)));
                }
            }
        }
    }
}

// BossHeroSkills._cast_w_dragon_tail L1490
void MysticHeroSkills::bosshero_cast_w_dragon_tail(Object* h, const Array& enemies) {
    Variant dist;
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 40);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 130)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_e_dragon_blood L1502
void MysticHeroSkills::bosshero_cast_e_dragon_blood(Object* h) {
    Variant base_damage;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    set_kit_value(h, "dragon_blood_active", true);
    set_kit_value(h, "dragon_blood_timer", 480);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.3)));
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.2));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_elder_dragon_form L1516
void MysticHeroSkills::bosshero_cast_r_elder_dragon_form(Object* h, const Array& enemies) {
    Variant base_damage;
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    set_kit_value(h, "dragon_form_active", true);
    set_kit_value(h, "dragon_form_timer", 600);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.8)));
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 3.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(90)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.25));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_krobellus_exorcism L1541
void MysticHeroSkills::bosshero_cast_q_krobellus_exorcism(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 50);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
    kit_fx_cast(h, "q");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 150, "q");
}

// BossHeroSkills._cast_w_krobellus_silence L1554
void MysticHeroSkills::bosshero_cast_w_krobellus_silence(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
    kit_fx_cast(h, "w");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 120, "w");
}

// BossHeroSkills._cast_e_krobellus_siphon L1569
void MysticHeroSkills::bosshero_cast_e_krobellus_siphon(Object* h) {
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
        heal = (int64_t)(((double)(kit_skill_damage(h)) * 0.5));
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
        kit_fx_cast(h, "e");
        kit_fx_impact(h, get_global_pos_x(get_target(h)), get_global_pos_y(get_target(h)), 44, "e");
    }
}

// BossHeroSkills._cast_r_krobellus_crypt L1584
void MysticHeroSkills::bosshero_cast_r_krobellus_crypt(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.5))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
    kit_fx_cast(h, "r");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 200, "r");
}

// BossHeroSkills._cast_q_vhalzun_death_pulse L1606
void MysticHeroSkills::bosshero_cast_q_vhalzun_death_pulse(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 130)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
    kit_fx_cast(h, "q");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 130, "q");
}

// BossHeroSkills._cast_w_vhalzun_heartstopper L1619
void MysticHeroSkills::bosshero_cast_w_vhalzun_heartstopper(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
    kit_fx_cast(h, "w");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 150, "w");
}

// BossHeroSkills._cast_e_vhalzun_reapers_scythe L1634
void MysticHeroSkills::bosshero_cast_e_vhalzun_reapers_scythe(Object* h, const Array& enemies) {
    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
    }
    kit_fx_cast(h, "e");
}

// BossHeroSkills._cast_r_vhalzun_ghost_shroud L1645
void MysticHeroSkills::bosshero_cast_r_vhalzun_ghost_shroud(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 100);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.18));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
    kit_fx_cast(h, "r");
    kit_fx_impact(h, get_global_pos_x(h), get_global_pos_y(h), 150, "r");
}

// BossHeroSkills._cast_q_kunkka_tide L1663
void MysticHeroSkills::bosshero_cast_q_kunkka_tide(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant perp;
    Variant proj;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 250)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 70)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            }
        }
    }
}

// BossHeroSkills._cast_w_kunkka_xmark L1675
void MysticHeroSkills::bosshero_cast_w_kunkka_xmark(Object* h, const Array& enemies) {
    Variant e;
    Variant tx;
    Variant ty;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 80);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
        for (int __i=0; __i< (int)(enemies.size()); ++__i) {
            Variant __v_e = enemies[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 120)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
                if (kit_has_atk_timer(h, e)) {
                    kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
                }
            }
        }
    }
}

// BossHeroSkills._cast_e_kunkka_ghost L1685
void MysticHeroSkills::bosshero_cast_e_kunkka_ghost(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant heal;
    Variant perp;
    Variant proj;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 90);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 300)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 80)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.2))), get_team(h), Variant(), "");
                if (kit_has_atk_timer(h, e)) {
                    kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(90)));
                }
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_kunkka_torrent L1701
void MysticHeroSkills::bosshero_cast_r_kunkka_torrent(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;
    Variant tx;
    Variant ty;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 100);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = get_global_pos_x(h);
        ty = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 3.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(120)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.2));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_nyxarath_shadowraze L1718
void MysticHeroSkills::bosshero_cast_q_nyxarath_shadowraze(Object* h, const Array& enemies) {
    Variant closest;
    Variant closest_dist;
    Variant d;
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant perp;
    Variant proj;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    closest = Variant();
    closest_dist = 9999;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        d = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(d) < (double)(closest_dist))) {
            closest_dist = d;
            closest = e;
        }
    }
    if (py_or(!(closest), ((double)(closest_dist) > 300))) {
        return;
    }
    dx = ((double)(get_global_pos_x(closest)) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(closest)) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 280)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 50)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
                if (kit_has_atk_timer(h, e)) {
                    kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(45)));
                }
            }
        }
    }
}

// BossHeroSkills._cast_w_nyxarath_necro L1738
void MysticHeroSkills::bosshero_cast_w_nyxarath_necro(Object* h, const Array& enemies) {
    Variant base_damage;
    Variant e;
    Variant heal;
    Variant kills;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 70);
    kills = 0;
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 180)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.7))), get_team(h), Variant(), "");
            if (!(kit_unit_alive(h, e))) {
                kills = (double)(kills) + (double)(1);
            }
        }
    }
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.4)));
    set_kit_value(h, "rage_active", true);
    set_kit_value(h, "rage_timer", 480);
    heal = ((double)((int64_t)(((double)(get_max_hp(h)) * 0.08))) + (double)(((double)(kills) * 30)));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_nyxarath_presence L1752
void MysticHeroSkills::bosshero_cast_e_nyxarath_presence(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(90)));
            }
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 240);
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_nyxarath_requiem L1762
void MysticHeroSkills::bosshero_cast_r_nyxarath_requiem(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 110);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 3.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(120)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_gravewake_anchor L1775
void MysticHeroSkills::bosshero_cast_q_gravewake_anchor(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant perp;
    Variant proj;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 200)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 60)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
                if (kit_has_slow(h, e)) {
                    kit_slow(h, e, 0.5, 180);
                }
            }
        }
    }
}

// BossHeroSkills._cast_w_gravewake_tide L1790
void MysticHeroSkills::bosshero_cast_w_gravewake_tide(Object* h, const Array& enemies) {
    Variant e;
    Variant tx;
    Variant ty;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 80);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = get_global_pos_x(h);
        ty = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_e_gravewake_shell L1802
void MysticHeroSkills::bosshero_cast_e_gravewake_shell(Object* h) {
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 70);
    set_kit_value(h, "defense_boost", true);
    set_kit_value(h, "defense_timer", 300);
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_gravewake_ravage L1807
void MysticHeroSkills::bosshero_cast_r_gravewake_ravage(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 180);
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_syrentha_riptide L1820
void MysticHeroSkills::bosshero_cast_q_syrentha_riptide(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant perp;
    Variant proj;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 250)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 70)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
                if (kit_has_slow(h, e)) {
                    kit_slow(h, e, 0.5, 180);
                }
            }
        }
    }
}

// BossHeroSkills._cast_w_syrentha_song L1835
void MysticHeroSkills::bosshero_cast_w_syrentha_song(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(120)));
            }
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.7, 240);
            }
        }
    }
}

// BossHeroSkills._cast_e_syrentha_mirror L1845
void MysticHeroSkills::bosshero_cast_e_syrentha_mirror(Object* h) {
    Variant base_damage;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 70);
    set_kit_value(h, "rage_active", true);
    set_kit_value(h, "rage_timer", 360);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.4)));
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_syrentha_siren L1853
void MysticHeroSkills::bosshero_cast_r_syrentha_siren(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(150)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_thalgryn_waveform L1866
void MysticHeroSkills::bosshero_cast_q_thalgryn_waveform(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant ex;
    Variant ey;
    Variant perp;
    Variant proj;
    Variant surge;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 60);
    if (py_or(!(get_target(h)), !(kit_unit_alive(h, get_target(h))))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) == 0)) {
        return;
    }
    dx = (double)(dx) / (double)(dist);
    dy = (double)(dy) / (double)(dist);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
        if ((0 < (double)(proj)) && ((double)(proj) < 250)) {
            perp = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
            if (((double)(perp) < 50)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.6))), get_team(h), Variant(), "");
            }
        }
    }
    surge = MIN((double)(dist), (double)(200));
    set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(dx) * (double)(surge))));
    set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(dy) * (double)(surge))));
}

// BossHeroSkills._cast_w_thalgryn_adaptive L1879
void MysticHeroSkills::bosshero_cast_w_thalgryn_adaptive(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
        for (int __i=0; __i< (int)(enemies.size()); ++__i) {
            Variant __v_e = enemies[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (((e != get_target(h))) && (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(get_target(h)))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(get_target(h))))).length()) <= 60))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.7))), get_team(h), Variant(), "");
            }
        }
    }
}

// BossHeroSkills._cast_e_thalgryn_morph L1887
void MysticHeroSkills::bosshero_cast_e_thalgryn_morph(Object* h) {
    Variant base_damage;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    set_kit_value(h, "rage_active", true);
    set_kit_value(h, "rage_timer", 300);
    base_damage = kit_catalog_all(h)[get_hero_type(h)]["damage"];
    set_damage(h, (int64_t)(((double)(base_damage) * 1.35)));
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.14));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_thalgryn_replicate L1895
void MysticHeroSkills::bosshero_cast_r_thalgryn_replicate(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.4, 180);
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_malzareth_disruption L1908
void MysticHeroSkills::bosshero_cast_q_malzareth_disruption(Object* h, const Array& enemies) {
    Variant e;
    Variant tx;
    Variant ty;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 60);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = ((double)(get_global_pos_x(h)) + 100);
        ty = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_w_malzareth_soul L1918
void MysticHeroSkills::bosshero_cast_w_malzareth_soul(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
        for (int __i=0; __i< (int)(enemies.size()); ++__i) {
            Variant __v_e = enemies[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (((e != get_target(h))) && (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(get_target(h)))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(get_target(h))))).length()) <= 60))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.7))), get_team(h), Variant(), "");
            }
        }
    }
}

// BossHeroSkills._cast_e_malzareth_poison L1926
void MysticHeroSkills::bosshero_cast_e_malzareth_poison(Object* h, const Array& enemies) {
    set_active_skill(h, "e");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.5, 180);
        }
    }
}

// BossHeroSkills._cast_r_malzareth_disillusion L1933
void MysticHeroSkills::bosshero_cast_r_malzareth_disillusion(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(90)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_akashari_strike L1946
void MysticHeroSkills::bosshero_cast_q_akashari_strike(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.6))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.4, 120);
        }
    }
}

// BossHeroSkills._cast_w_akashari_blink L1953
void MysticHeroSkills::bosshero_cast_w_akashari_blink(Object* h, const Array& enemies) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > 0)) {
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(dist))) * (double)(MIN((double)(dist), (double)(150))))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(dist))) * (double)(MIN((double)(dist), (double)(150))))));
        }
        for (int __i=0; __i< (int)(enemies.size()); ++__i) {
            Variant __v_e = enemies[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 80)) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.08));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_akashari_scream L1964
void MysticHeroSkills::bosshero_cast_e_akashari_scream(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.5))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_akashari_sonic L1970
void MysticHeroSkills::bosshero_cast_r_akashari_sonic(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.3))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 240);
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_vorenmarr_bonds L1983
void MysticHeroSkills::bosshero_cast_q_vorenmarr_bonds(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 70);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
        for (int __i=0; __i< (int)(enemies.size()); ++__i) {
            Variant __v_e = enemies[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (((e != get_target(h))) && (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(get_target(h)))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(get_target(h))))).length()) <= 80))) {
                kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.6))), get_team(h), Variant(), "");
            }
        }
    }
}

// BossHeroSkills._cast_w_vorenmarr_power L1991
void MysticHeroSkills::bosshero_cast_w_vorenmarr_power(Object* h) {
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 70);
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.14));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_vorenmarr_upheaval L1995
void MysticHeroSkills::bosshero_cast_e_vorenmarr_upheaval(Object* h, const Array& enemies) {
    Variant e;
    Variant tx;
    Variant ty;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 80);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        tx = get_global_pos_x(get_target(h));
        ty = get_global_pos_y(get_target(h));
    } else {
        tx = get_global_pos_x(h);
        ty = get_global_pos_y(h);
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(tx)), ((double)(get_global_pos_y(e)) - (double)(ty))).length()) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_r_vorenmarr_golem L2007
void MysticHeroSkills::bosshero_cast_r_vorenmarr_golem(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 100);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(90)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_kenshiro_swiftslash L2021
void MysticHeroSkills::bosshero_cast_q_kenshiro_swiftslash(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_kenshiro_assault L2027
void MysticHeroSkills::bosshero_cast_w_kenshiro_assault(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(90));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_kenshiro_gale L2041
void MysticHeroSkills::bosshero_cast_e_kenshiro_gale(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_kenshiro_supremacy L2048
void MysticHeroSkills::bosshero_cast_r_kenshiro_supremacy(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 70);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_q_khazan_chained L2056
void MysticHeroSkills::bosshero_cast_q_khazan_chained(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_khazan_leap L2062
void MysticHeroSkills::bosshero_cast_w_khazan_leap(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant e;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(110));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 90)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_khazan_spin L2078
void MysticHeroSkills::bosshero_cast_e_khazan_spin(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 160)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_khazan_vanish L2085
void MysticHeroSkills::bosshero_cast_r_khazan_vanish(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 75);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.08));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_wiro_windcut L2095
void MysticHeroSkills::bosshero_cast_q_wiro_windcut(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 30);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_wiro_whirl L2101
void MysticHeroSkills::bosshero_cast_w_wiro_whirl(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 140)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_wiro_dash L2108
void MysticHeroSkills::bosshero_cast_e_wiro_dash(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(100));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_r_wiro_typhoon L2122
void MysticHeroSkills::bosshero_cast_r_wiro_typhoon(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 90);
            }
        }
    }
}

// BossHeroSkills._cast_q_naraka_chaos L2132
void MysticHeroSkills::bosshero_cast_q_naraka_chaos(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_naraka_shadowstep L2138
void MysticHeroSkills::bosshero_cast_w_naraka_shadowstep(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 50);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(120));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_naraka_hammer L2152
void MysticHeroSkills::bosshero_cast_e_naraka_hammer(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 180)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(30)));
            }
        }
    }
}

// BossHeroSkills._cast_r_naraka_execution L2161
void MysticHeroSkills::bosshero_cast_r_naraka_execution(Object* h, const Array& enemies) {
    Variant dmg;
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 230)) {
            dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.8));
            if (((double)(((double)(get_hp(e)) / (double)(MAX((double)(1), (double)(get_max_hp(e)))))) < 0.3)) {
                dmg = (int64_t)(((double)(dmg) * 1.6));
            }
            kit_hit(h, e, (int)(dmg), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_krognarr_strike L2179
void MysticHeroSkills::bosshero_cast_q_krognarr_strike(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_krognarr_seismic L2185
void MysticHeroSkills::bosshero_cast_w_krognarr_seismic(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(30)));
            }
        }
    }
}

// BossHeroSkills._cast_e_krognarr_rampart L2194
void MysticHeroSkills::bosshero_cast_e_krognarr_rampart(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.9))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.08));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_krognarr_eruption L2203
void MysticHeroSkills::bosshero_cast_r_krognarr_eruption(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_raz_overdrive L2213
void MysticHeroSkills::bosshero_cast_q_raz_overdrive(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_raz_searing L2219
void MysticHeroSkills::bosshero_cast_w_raz_searing(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(100));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_raz_surge L2233
void MysticHeroSkills::bosshero_cast_e_raz_surge(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 160)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_raz_gloom L2240
void MysticHeroSkills::bosshero_cast_r_raz_gloom(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(50)));
            }
        }
    }
}

// BossHeroSkills._cast_q_vraskhan_thorned L2250
void MysticHeroSkills::bosshero_cast_q_vraskhan_thorned(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(90));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_vraskhan_leap L2264
void MysticHeroSkills::bosshero_cast_w_vraskhan_leap(Object* h, const Array& enemies) {
    set_active_skill(h, "w");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_global_pos_x(h, (double)(get_global_pos_x(get_target(h))));
        set_global_pos_y(h, (double)(((double)(get_global_pos_y(get_target(h))) - 20)));
        set_facing(h, (((double)(get_global_pos_x(get_target(h))) > (double)(get_global_pos_x(h))) ? 1 : -(1)));
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_vraskhan_deathslash L2273
void MysticHeroSkills::bosshero_cast_e_vraskhan_deathslash(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_vraskhan_omni L2280
void MysticHeroSkills::bosshero_cast_r_vraskhan_omni(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_aurethzar_marksman L2290
void MysticHeroSkills::bosshero_cast_q_aurethzar_marksman(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aurethzar_piercing L2296
void MysticHeroSkills::bosshero_cast_w_aurethzar_piercing(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_aurethzar_frost L2303
void MysticHeroSkills::bosshero_cast_e_aurethzar_frost(Object* h, const Array& enemies) {
    set_active_skill(h, "e");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.5, 90);
        }
    }
}

// BossHeroSkills._cast_r_aurethzar_thunder L2311
void MysticHeroSkills::bosshero_cast_r_aurethzar_thunder(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_aeralith_tailwind L2325
void MysticHeroSkills::bosshero_cast_q_aeralith_tailwind(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aeralith_windblade L2331
void MysticHeroSkills::bosshero_cast_w_aeralith_windblade(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_aeralith_vacuum L2338
void MysticHeroSkills::bosshero_cast_e_aeralith_vacuum(Object* h, const Array& enemies) {
    Variant d;
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        d = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(d) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_aeralith_skyrider L2348
void MysticHeroSkills::bosshero_cast_r_aeralith_skyrider(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 240)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_q_aurex_shieldcrash L2356
void MysticHeroSkills::bosshero_cast_q_aurex_shieldcrash(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aurex_voltblast L2362
void MysticHeroSkills::bosshero_cast_w_aurex_voltblast(Object* h, const Array& enemies) {
    set_active_skill(h, "w");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_aurex_aegis L2368
void MysticHeroSkills::bosshero_cast_e_aurex_aegis(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 130)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.9))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_aurex_spin L2377
void MysticHeroSkills::bosshero_cast_r_aurex_spin(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 75);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_nyxareva_darkslash L2387
void MysticHeroSkills::bosshero_cast_q_nyxareva_darkslash(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_nyxareva_mortalwound L2393
void MysticHeroSkills::bosshero_cast_w_nyxareva_mortalwound(Object* h, const Array& enemies) {
    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.4))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.5, 90);
        }
    }
}

// BossHeroSkills._cast_e_nyxareva_sacrifice L2401
void MysticHeroSkills::bosshero_cast_e_nyxareva_sacrifice(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_nyxareva_avatar L2408
void MysticHeroSkills::bosshero_cast_r_nyxareva_avatar(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_thalakryon_bolt L2418
void MysticHeroSkills::bosshero_cast_q_thalakryon_bolt(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_thalakryon_aquashield L2424
void MysticHeroSkills::bosshero_cast_w_thalakryon_aquashield(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_thalakryon_tidalrage L2433
void MysticHeroSkills::bosshero_cast_e_thalakryon_tidalrage(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(40)));
            }
        }
    }
}

// BossHeroSkills._cast_r_thalakryon_metamorph L2442
void MysticHeroSkills::bosshero_cast_r_thalakryon_metamorph(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 260)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_aurelix_timebomb L2458
void MysticHeroSkills::bosshero_cast_q_aurelix_timebomb(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aurelix_will L2464
void MysticHeroSkills::bosshero_cast_w_aurelix_will(Object* h, const Array& enemies) {
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 60);
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_aurelix_shockwave L2470
void MysticHeroSkills::bosshero_cast_e_aurelix_shockwave(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(40)));
            }
        }
    }
}

// BossHeroSkills._cast_r_aurelix_transcend L2479
void MysticHeroSkills::bosshero_cast_r_aurelix_transcend(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 240)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 90);
            }
        }
    }
}

// BossHeroSkills._cast_q_aurelyssa_whirlwind L2489
void MysticHeroSkills::bosshero_cast_q_aurelyssa_whirlwind(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 140)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_w_aurelyssa_sweep L2496
void MysticHeroSkills::bosshero_cast_w_aurelyssa_sweep(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 160)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_aurelyssa_wings L2503
void MysticHeroSkills::bosshero_cast_e_aurelyssa_wings(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant e;
    Variant step;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(100));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 120)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_aurelyssa_phantom L2519
void MysticHeroSkills::bosshero_cast_r_aurelyssa_phantom(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_vargrath_bloodthirst L2529
void MysticHeroSkills::bosshero_cast_q_vargrath_bloodthirst(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_vargrath_charge L2535
void MysticHeroSkills::bosshero_cast_w_vargrath_charge(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant e;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(110));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
    }
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 100)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_vargrath_devilstrike L2551
void MysticHeroSkills::bosshero_cast_e_vargrath_devilstrike(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_vargrath_souldom L2558
void MysticHeroSkills::bosshero_cast_r_vargrath_souldom(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 230)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_nazulmor_typhoon L2568
void MysticHeroSkills::bosshero_cast_q_nazulmor_typhoon(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_w_nazulmor_aquashield L2575
void MysticHeroSkills::bosshero_cast_w_nazulmor_aquashield(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 150)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_nazulmor_tidalrage L2584
void MysticHeroSkills::bosshero_cast_e_nazulmor_tidalrage(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(40)));
            }
        }
    }
}

// BossHeroSkills._cast_r_nazulmor_chaotic L2593
void MysticHeroSkills::bosshero_cast_r_nazulmor_chaotic(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 270)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_kaeldris_overwhelming L2609
void MysticHeroSkills::bosshero_cast_q_kaeldris_overwhelming(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_kaeldris_press L2615
void MysticHeroSkills::bosshero_cast_w_kaeldris_press(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(110));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_kaeldris_moment L2629
void MysticHeroSkills::bosshero_cast_e_kaeldris_moment(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_kaeldris_duel L2636
void MysticHeroSkills::bosshero_cast_r_kaeldris_duel(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_pyraklos_spearmars L2646
void MysticHeroSkills::bosshero_cast_q_pyraklos_spearmars(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_pyraklos_rebuke L2652
void MysticHeroSkills::bosshero_cast_w_pyraklos_rebuke(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_pyraklos_bulwark L2659
void MysticHeroSkills::bosshero_cast_e_pyraklos_bulwark(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 130)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.7))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_pyraklos_arena L2668
void MysticHeroSkills::bosshero_cast_r_pyraklos_arena(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 230)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.8))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(60)));
            }
        }
    }
}

// BossHeroSkills._cast_q_velmyrth_dagger L2678
void MysticHeroSkills::bosshero_cast_q_velmyrth_dagger(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 35);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.5, 90);
        }
    }
}

// BossHeroSkills._cast_w_velmyrth_strike L2686
void MysticHeroSkills::bosshero_cast_w_velmyrth_strike(Object* h, const Array& enemies) {
    set_active_skill(h, "w");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_global_pos_x(h, (double)(get_global_pos_x(get_target(h))));
        set_global_pos_y(h, (double)(((double)(get_global_pos_y(get_target(h))) - 20)));
        set_facing(h, (((double)(get_global_pos_x(get_target(h))) > (double)(get_global_pos_x(h))) ? 1 : -(1)));
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_e_velmyrth_blur L2695
void MysticHeroSkills::bosshero_cast_e_velmyrth_blur(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_velmyrth_coup L2702
void MysticHeroSkills::bosshero_cast_r_velmyrth_coup(Object* h, const Array& enemies) {
    Variant dmg;
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 80);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.8));
            if (((double)(((double)(get_hp(e)) / (double)(MAX((double)(1), (double)(get_max_hp(e)))))) < 0.3)) {
                dmg = (int64_t)(((double)(dmg) * 1.6));
            }
            kit_hit(h, e, (int)(dmg), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_q_solvarin_purification L2714
void MysticHeroSkills::bosshero_cast_q_solvarin_purification(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_solvarin_repel L2720
void MysticHeroSkills::bosshero_cast_w_solvarin_repel(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 180)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(40)));
            }
        }
    }
}

// BossHeroSkills._cast_e_solvarin_degen L2729
void MysticHeroSkills::bosshero_cast_e_solvarin_degen(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.9))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.4, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_solvarin_guardian L2738
void MysticHeroSkills::bosshero_cast_r_solvarin_guardian(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_azureth_arcanebolt L2750
void MysticHeroSkills::bosshero_cast_q_azureth_arcanebolt(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_azureth_concussive L2756
void MysticHeroSkills::bosshero_cast_w_azureth_concussive(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 170)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_azureth_ancientseal L2763
void MysticHeroSkills::bosshero_cast_e_azureth_ancientseal(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 100);
            }
        }
    }
}

// BossHeroSkills._cast_r_azureth_mysticflare L2772
void MysticHeroSkills::bosshero_cast_r_azureth_mysticflare(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 85);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 240)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(65)));
            }
        }
    }
}

// BossHeroSkills._cast_q_luminar_illuminate L2782
void MysticHeroSkills::bosshero_cast_q_luminar_illuminate(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_luminar_blindinglight L2788
void MysticHeroSkills::bosshero_cast_w_luminar_blindinglight(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(45)));
            }
        }
    }
}

// BossHeroSkills._cast_e_luminar_wisp L2797
void MysticHeroSkills::bosshero_cast_e_luminar_wisp(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_luminar_spiritform L2804
void MysticHeroSkills::bosshero_cast_r_luminar_spiritform(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_solara_starbreaker L2814
void MysticHeroSkills::bosshero_cast_q_solara_starbreaker(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_solara_celestialhammer L2820
void MysticHeroSkills::bosshero_cast_w_solara_celestialhammer(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 185)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_solara_luminosity L2827
void MysticHeroSkills::bosshero_cast_e_solara_luminosity(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.95))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_r_solara_solarguardian L2836
void MysticHeroSkills::bosshero_cast_r_solara_solarguardian(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 240)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_pyraethis_icarusdive L2846
void MysticHeroSkills::bosshero_cast_q_pyraethis_icarusdive(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_pyraethis_firespirits L2855
void MysticHeroSkills::bosshero_cast_w_pyraethis_firespirits(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_pyraethis_sunray L2862
void MysticHeroSkills::bosshero_cast_e_pyraethis_sunray(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.35, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_pyraethis_supernova L2871
void MysticHeroSkills::bosshero_cast_r_pyraethis_supernova(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 300)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.1))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_auroth_ionicedge L2883
void MysticHeroSkills::bosshero_cast_q_auroth_ionicedge(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_auroth_ward L2889
void MysticHeroSkills::bosshero_cast_w_auroth_ward(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 185)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.1))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_auroth_consecration L2898
void MysticHeroSkills::bosshero_cast_e_auroth_consecration(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.4, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_auroth_guardian L2907
void MysticHeroSkills::bosshero_cast_r_auroth_guardian(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 240)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_morvein_puncture L2917
void MysticHeroSkills::bosshero_cast_q_morvein_puncture(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_morvein_violentstrike L2926
void MysticHeroSkills::bosshero_cast_w_morvein_violentstrike(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_morvein_spectralcharge L2933
void MysticHeroSkills::bosshero_cast_e_morvein_spectralcharge(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_morvein_phantomform L2940
void MysticHeroSkills::bosshero_cast_r_morvein_phantomform(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_thorvak_seed L2950
void MysticHeroSkills::bosshero_cast_q_thorvak_seed(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.4, 90);
        }
    }
}

// BossHeroSkills._cast_w_thorvak_natureswrath L2958
void MysticHeroSkills::bosshero_cast_w_thorvak_natureswrath(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_thorvak_vengeance L2965
void MysticHeroSkills::bosshero_cast_e_thorvak_vengeance(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_thorvak_dryad L2972
void MysticHeroSkills::bosshero_cast_r_thorvak_dryad(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.1));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_yamako_deepforest L2984
void MysticHeroSkills::bosshero_cast_q_yamako_deepforest(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.4));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_yamako_woodcreation L2993
void MysticHeroSkills::bosshero_cast_w_yamako_woodcreation(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_yamako_woodgolem L3000
void MysticHeroSkills::bosshero_cast_e_yamako_woodgolem(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(50)));
            }
        }
    }
}

// BossHeroSkills._cast_r_yamako_kannon L3009
void MysticHeroSkills::bosshero_cast_r_yamako_kannon(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 300)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.1))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_ignirus_searingtorrent L3021
void MysticHeroSkills::bosshero_cast_q_ignirus_searingtorrent(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_ignirus_flameshot L3027
void MysticHeroSkills::bosshero_cast_w_ignirus_flameshot(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_ignirus_burstfireball L3034
void MysticHeroSkills::bosshero_cast_e_ignirus_burstfireball(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.35, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_ignirus_vengeance L3043
void MysticHeroSkills::bosshero_cast_r_ignirus_vengeance(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_leoric_fearlesscharge L3053
void MysticHeroSkills::bosshero_cast_q_leoric_fearlesscharge(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(100));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_leoric_sacredhammer L3067
void MysticHeroSkills::bosshero_cast_w_leoric_sacredhammer(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_leoric_concealblast L3074
void MysticHeroSkills::bosshero_cast_e_leoric_concealblast(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(50)));
            }
        }
    }
}

// BossHeroSkills._cast_r_leoric_immortality L3083
void MysticHeroSkills::bosshero_cast_r_leoric_immortality(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.2));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_shirotaka_hiraishin L3093
void MysticHeroSkills::bosshero_cast_q_shirotaka_hiraishin(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_global_pos_x(h, (double)(get_global_pos_x(get_target(h))));
        set_global_pos_y(h, (double)(((double)(get_global_pos_y(get_target(h))) - 20)));
        set_facing(h, (((double)(get_global_pos_x(get_target(h))) > (double)(get_global_pos_x(h))) ? 1 : -(1)));
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_shirotaka_waterboundary L3105
void MysticHeroSkills::bosshero_cast_w_shirotaka_waterboundary(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 90);
            }
        }
    }
}

// BossHeroSkills._cast_e_shirotaka_shadowclones L3114
void MysticHeroSkills::bosshero_cast_e_shirotaka_shadowclones(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_shirotaka_paperbomb L3121
void MysticHeroSkills::bosshero_cast_r_shirotaka_paperbomb(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_seiryukong_boundless L3131
void MysticHeroSkills::bosshero_cast_q_seiryukong_boundless(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.4));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_seiryukong_treedance L3140
void MysticHeroSkills::bosshero_cast_w_seiryukong_treedance(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_seiryukong_jingusoldiers L3147
void MysticHeroSkills::bosshero_cast_e_seiryukong_jingusoldiers(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_seiryukong_wukong L3156
void MysticHeroSkills::bosshero_cast_r_seiryukong_wukong(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 300)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.15))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_kaelthorn_bravestfighter L3168
void MysticHeroSkills::bosshero_cast_q_kaelthorn_bravestfighter(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(110));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_kaelthorn_justiceblade L3182
void MysticHeroSkills::bosshero_cast_w_kaelthorn_justiceblade(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_kaelthorn_defendersassault L3189
void MysticHeroSkills::bosshero_cast_e_kaelthorn_defendersassault(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_kaelthorn_chivalryfists L3196
void MysticHeroSkills::bosshero_cast_r_kaelthorn_chivalryfists(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.9))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_solvanth_ringpunishment L3206
void MysticHeroSkills::bosshero_cast_q_solvanth_ringpunishment(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_solvanth_gloriouspathway L3212
void MysticHeroSkills::bosshero_cast_w_solvanth_gloriouspathway(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.4, 90);
            }
        }
    }
}

// BossHeroSkills._cast_e_solvanth_laworder L3221
void MysticHeroSkills::bosshero_cast_e_solvanth_laworder(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_solvanth_wrath L3228
void MysticHeroSkills::bosshero_cast_r_solvanth_wrath(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 260)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_xyrael_finch L3238
void MysticHeroSkills::bosshero_cast_q_xyrael_finch(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_global_pos_x(h, (double)(get_global_pos_x(get_target(h))));
        set_global_pos_y(h, (double)(((double)(get_global_pos_y(get_target(h))) - 20)));
        set_facing(h, (((double)(get_global_pos_x(get_target(h))) > (double)(get_global_pos_x(h))) ? 1 : -(1)));
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_xyrael_defiant L3250
void MysticHeroSkills::bosshero_cast_w_xyrael_defiant(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_xyrael_tempest L3257
void MysticHeroSkills::bosshero_cast_e_xyrael_tempest(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_xyrael_lightness L3264
void MysticHeroSkills::bosshero_cast_r_xyrael_lightness(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
}

// BossHeroSkills._cast_q_nyxareth_starsplit L3276
void MysticHeroSkills::bosshero_cast_q_nyxareth_starsplit(Object* h, const Array& enemies) {
    set_active_skill(h, "1");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_nyxareth_realworld L3282
void MysticHeroSkills::bosshero_cast_w_nyxareth_realworld(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "2");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_nyxareth_spacetime L3289
void MysticHeroSkills::bosshero_cast_e_nyxareth_spacetime(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "3");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_nyxareth_astrorealm L3298
void MysticHeroSkills::bosshero_cast_r_nyxareth_astrorealm(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "4");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 300)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_cryssalia_frostshock L3310
void MysticHeroSkills::bosshero_cast_q_cryssalia_frostshock(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_cryssalia_bitterfrost L3316
void MysticHeroSkills::bosshero_cast_w_cryssalia_bitterfrost(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 90);
            }
        }
    }
}

// BossHeroSkills._cast_e_cryssalia_frostbites L3325
void MysticHeroSkills::bosshero_cast_e_cryssalia_frostbites(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 215)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_cryssalia_coldest L3332
void MysticHeroSkills::bosshero_cast_r_cryssalia_coldest(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 120);
            }
        }
    }
}

// BossHeroSkills._cast_q_kaelthar_chargingfist L3342
void MysticHeroSkills::bosshero_cast_q_kaelthar_chargingfist(Object* h, const Array& enemies) {
    Variant d;
    Variant dx;
    Variant dy;
    Variant step;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        d = Vector2(dx, dy).length();
        if (((double)(d) > 1)) {
            step = MIN((double)(d), (double)(110));
            set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(((double)(dx) / (double)(d))) * (double)(step))));
            set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(((double)(dy) / (double)(d))) * (double)(step))));
            set_facing(h, (((double)(dx) > 0) ? 1 : -(1)));
        }
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.3))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_kaelthar_quake L3356
void MysticHeroSkills::bosshero_cast_w_kaelthar_quake(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 190)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_kaelthar_fistcrack L3363
void MysticHeroSkills::bosshero_cast_e_kaelthar_fistcrack(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_kaelthar_fistbreak L3370
void MysticHeroSkills::bosshero_cast_r_kaelthar_fistbreak(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 250)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
}

// BossHeroSkills._cast_q_morkhaera_spiritburst L3380
void MysticHeroSkills::bosshero_cast_q_morkhaera_spiritburst(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_morkhaera_airstrike L3386
void MysticHeroSkills::bosshero_cast_w_morkhaera_airstrike(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_morkhaera_energyimpact L3393
void MysticHeroSkills::bosshero_cast_e_morkhaera_energyimpact(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 215)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_morkhaera_ethereal L3402
void MysticHeroSkills::bosshero_cast_r_morkhaera_ethereal(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_aurelion_callcourage L3412
void MysticHeroSkills::bosshero_cast_q_aurelion_callcourage(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.4));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_aurelion_guardianassault L3421
void MysticHeroSkills::bosshero_cast_w_aurelion_guardianassault(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_aurelion_kingscommand L3428
void MysticHeroSkills::bosshero_cast_e_aurelion_kingscommand(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 225)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.35, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_aurelion_kingssummon L3437
void MysticHeroSkills::bosshero_cast_r_aurelion_kingssummon(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 300)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.2))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_akahime_petalbarrage L3449
void MysticHeroSkills::bosshero_cast_q_akahime_petalbarrage(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_akahime_soulscroll L3455
void MysticHeroSkills::bosshero_cast_w_akahime_soulscroll(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.4, 90);
            }
        }
    }
}

// BossHeroSkills._cast_e_akahime_shadow L3464
void MysticHeroSkills::bosshero_cast_e_akahime_shadow(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_akahime_higanbana L3471
void MysticHeroSkills::bosshero_cast_r_akahime_higanbana(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 270)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_nyxthrael_ambush L3481
void MysticHeroSkills::bosshero_cast_q_nyxthrael_ambush(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_nyxthrael_nightfall L3490
void MysticHeroSkills::bosshero_cast_w_nyxthrael_nightfall(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_nyxthrael_darknightfall L3497
void MysticHeroSkills::bosshero_cast_e_nyxthrael_darknightfall(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_nyxthrael_shadowbringer L3506
void MysticHeroSkills::bosshero_cast_r_nyxthrael_shadowbringer(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 260)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
}

// BossHeroSkills._cast_q_sylvantheros_sprout L3516
void MysticHeroSkills::bosshero_cast_q_sylvantheros_sprout(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.4, 90);
        }
    }
}

// BossHeroSkills._cast_w_sylvantheros_teleport L3524
void MysticHeroSkills::bosshero_cast_w_sylvantheros_teleport(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_sylvantheros_treants L3531
void MysticHeroSkills::bosshero_cast_e_sylvantheros_treants(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 215)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_sylvantheros_wrath L3538
void MysticHeroSkills::bosshero_cast_r_sylvantheros_wrath(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 280)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_vaelindra_energywave L3548
void MysticHeroSkills::bosshero_cast_q_vaelindra_energywave(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.4));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_vaelindra_spacering L3557
void MysticHeroSkills::bosshero_cast_w_vaelindra_spacering(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 215)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_vaelindra_violetrequiem L3564
void MysticHeroSkills::bosshero_cast_e_vaelindra_violetrequiem(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 230)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.35, 90);
            }
        }
    }
}

// BossHeroSkills._cast_r_vaelindra_realm L3573
void MysticHeroSkills::bosshero_cast_r_vaelindra_realm(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 310)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.25))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.12));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_q_astraelion_swordfall L3585
void MysticHeroSkills::bosshero_cast_q_astraelion_swordfall(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.5));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_astraelion_spiritblade L3594
void MysticHeroSkills::bosshero_cast_w_astraelion_spiritblade(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 195)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_astraelion_forceescape L3601
void MysticHeroSkills::bosshero_cast_e_astraelion_forceescape(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_astraelion_zeroreturn L3610
void MysticHeroSkills::bosshero_cast_r_astraelion_zeroreturn(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 260)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
}

// BossHeroSkills._cast_q_morvaenthir_soulfragment L3620
void MysticHeroSkills::bosshero_cast_q_morvaenthir_soulfragment(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_morvaenthir_spiritbind L3626
void MysticHeroSkills::bosshero_cast_w_morvaenthir_spiritbind(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 205)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
            if (kit_has_slow(h, e)) {
                kit_slow(h, e, 0.5, 100);
            }
        }
    }
}

// BossHeroSkills._cast_e_morvaenthir_essence L3635
void MysticHeroSkills::bosshero_cast_e_morvaenthir_essence(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 220)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_morvaenthir_shadowrealm L3642
void MysticHeroSkills::bosshero_cast_r_morvaenthir_shadowrealm(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 290)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(75)));
            }
        }
    }
}

// BossHeroSkills._cast_q_thornvaegrim_bramble L3652
void MysticHeroSkills::bosshero_cast_q_thornvaegrim_bramble(Object* h, const Array& enemies) {
    set_active_skill(h, "q");
    set_active_skill_timer(h, 40);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.25))), get_team(h), Variant(), "");
        if (kit_has_slow(h, get_target(h))) {
            kit_slow(h, get_target(h), 0.4, 90);
        }
    }
}

// BossHeroSkills._cast_w_thornvaegrim_twistedadvance L3660
void MysticHeroSkills::bosshero_cast_w_thornvaegrim_twistedadvance(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 200)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.15))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_e_thornvaegrim_saplingthrow L3667
void MysticHeroSkills::bosshero_cast_e_thornvaegrim_saplingthrow(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 60);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 215)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.0))), get_team(h), Variant(), "");
        }
    }
}

// BossHeroSkills._cast_r_thornvaegrim_grasp L3674
void MysticHeroSkills::bosshero_cast_r_thornvaegrim_grasp(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 90);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 270)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.95))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(70)));
            }
        }
    }
}

// BossHeroSkills._cast_q_morthraxis_batimpale L3684
void MysticHeroSkills::bosshero_cast_q_morthraxis_batimpale(Object* h, const Array& enemies) {
    Variant dmg;

    set_active_skill(h, "q");
    set_active_skill_timer(h, 45);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dmg = (int64_t)(((double)(kit_skill_damage(h)) * 1.3));
        if (((double)(((double)(get_hp(get_target(h))) / (double)(MAX((double)(1), (double)(get_max_hp(get_target(h))))))) < 0.3)) {
            dmg = (int64_t)(((double)(dmg) * 1.4));
        }
        kit_hit(h, get_target(h), (int)(dmg), get_team(h), Variant(), "");
    }
}

// BossHeroSkills._cast_w_morthraxis_sanguine L3693
void MysticHeroSkills::bosshero_cast_w_morthraxis_sanguine(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "w");
    set_active_skill_timer(h, 55);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 210)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.08));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// BossHeroSkills._cast_e_morthraxis_phantommob L3702
void MysticHeroSkills::bosshero_cast_e_morthraxis_phantommob(Object* h, const Array& enemies) {
    Variant e;

    set_active_skill(h, "e");
    set_active_skill_timer(h, 65);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 225)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.05))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(55)));
            }
        }
    }
}

// BossHeroSkills._cast_r_morthraxis_baleful L3711
void MysticHeroSkills::bosshero_cast_r_morthraxis_baleful(Object* h, const Array& enemies) {
    Variant e;
    Variant heal;

    set_active_skill(h, "r");
    set_active_skill_timer(h, 95);
    for (int __i=0; __i< (int)(enemies.size()); ++__i) {
        Variant __v_e = enemies[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        if (((double)(Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length()) <= 310)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.25))), get_team(h), Variant(), "");
            if (kit_has_atk_timer(h, e)) {
                kit_lock(h, e, MAX((double)(kit_atk_timer(h, e)), (double)(80)));
            }
        }
    }
    heal = (int64_t)(((double)(get_max_hp(h)) * 0.15));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + (double)(heal)))));
}

// GrimjawSkills.init_state L3753
void MysticHeroSkills::grimjaw_init_state(Object* h) {
    set_kit_value(h, "_blade_fury_active", false);
    set_kit_value(h, "_blade_fury_timer", 0);
    set_kit_value(h, "_heal_ward_active", false);
    set_kit_value(h, "_heal_ward_timer", 0);
    set_kit_value(h, "_heal_ward_pos", make_array(0, 0));
    set_kit_value(h, "_omnislash_active", false);
    set_kit_value(h, "_omnislash_timer", 0);
    set_kit_value(h, "_omnislash_target", Variant());
    set_kit_value(h, "_crit_buff_active", false);
    set_kit_value(h, "_crit_buff_timer", 0);
    set_kit_value(h, "_rage_active", false);
    set_kit_value(h, "_rage_timer", 0);
    set_kit_value(h, "_war_cry_timer", 0);
}

// GrimjawSkills.update_timers L3780
void MysticHeroSkills::grimjaw_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant d;
    Variant dist;
    Variant dist_ward;
    Variant e;
    Variant enemies;
    Variant spin_range;
    Variant u;

    if (((double)(get_kit_value(h, "_blade_fury_timer")) > 0)) {
        set_kit_value(h, "_blade_fury_timer", (int)get_kit_value(h, "_blade_fury_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "_blade_fury_timer")), (double)(15))) == 0)) {
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            spin_range = get_skill_data(h).get(Variant("skill_range"), 80);
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
                if (((double)(dist) <= (double)(spin_range))) {
                    kit_hit(h, e, (int)(kit_skill_damage(h)), get_team(h), h, "");
                }
            }
        }
        if (((double)(get_kit_value(h, "_blade_fury_timer")) <= 0)) {
            set_kit_value(h, "_blade_fury_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_heal_ward_timer")) > 0)) {
        set_kit_value(h, "_heal_ward_timer", (int)get_kit_value(h, "_heal_ward_timer") - (int)(1));
        dist_ward = Vector2(((double)(get_global_pos_x(h)) - (double)(((Array)(get_kit_value(h, "_heal_ward_pos")))[0])), ((double)(get_global_pos_y(h)) - (double)(((Array)(get_kit_value(h, "_heal_ward_pos")))[1]))).length();
        if ((((double)(dist_ward) <= 100)) && (((double)(get_hp(h)) < (double)(get_max_hp(h))))) {
            set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 2))));
        }
        for (int __i=0; __i< (int)(all_units.size()); ++__i) {
            Variant __v_u = all_units[__i];
            Object* u = nullptr; if (__v_u.get_type()==Variant::OBJECT) u = Object::cast_to<Object>(__v_u); if (!u) continue;
            if (((get_team(u) == get_team(h))) && (kit_unit_alive(h, u)) && ((u != h))) {
                d = Vector2(((double)(get_global_pos_x(u)) - (double)(((Array)(get_kit_value(h, "_heal_ward_pos")))[0])), ((double)(get_global_pos_y(u)) - (double)(((Array)(get_kit_value(h, "_heal_ward_pos")))[1]))).length();
                if ((((double)(d) <= 100)) && (kit_has_hp(h, u))) {
                    u->set("hp", MIN((double)(get_max_hp(u)), (double)(((double)(get_hp(u)) + 1))));
                }
            }
        }
        if (((double)(get_kit_value(h, "_heal_ward_timer")) <= 0)) {
            set_kit_value(h, "_heal_ward_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_omnislash_timer")) > 0)) {
        set_kit_value(h, "_omnislash_timer", (int)get_kit_value(h, "_omnislash_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "_omnislash_timer")), (double)(8))) == 0)) {
            if ((get_kit_value(h, "_omnislash_target")) && (kit_unit_alive(h, get_kit_value(h, "_omnislash_target")))) {
                kit_hit(h, get_kit_value(h, "_omnislash_target"), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.6))), get_team(h), h, "");
            }
        }
        if (((double)(get_kit_value(h, "_omnislash_timer")) <= 0)) {
            set_kit_value(h, "_omnislash_active", false);
            set_kit_value(h, "_omnislash_target", Variant());
        }
    }
    if (((double)(get_kit_value(h, "_crit_buff_timer")) > 0)) {
        set_kit_value(h, "_crit_buff_timer", (int)get_kit_value(h, "_crit_buff_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_crit_buff_timer")) <= 0)) {
            set_kit_value(h, "_crit_buff_active", false);
        }
    }
}

// GrimjawSkills.cast_q L3848
bool MysticHeroSkills::grimjaw_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_blade_fury_active", true);
    set_kit_value(h, "_blade_fury_timer", 180);
    trigger_q(h, "grimjaw", 8, Variant());
    return true;
}

// GrimjawSkills.cast_w L3869
bool MysticHeroSkills::grimjaw_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    set_kit_value(h, "_heal_ward_active", true);
    set_kit_value(h, "_heal_ward_timer", 360);
    set_kit_value(h, "_heal_ward_pos", make_array(get_global_pos_x(h), get_global_pos_y(h)));
    set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 30))));
    trigger_w(h, "grimjaw", 5, Variant());
    return true;
}

// GrimjawSkills.cast_e L3889
bool MysticHeroSkills::grimjaw_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_crit_buff_active", true);
    set_kit_value(h, "_crit_buff_timer", 300);
    deal_aoe(h, all_units, all_towers, all_bases, 60, 1.5);
    trigger_e(h, "grimjaw", 6, Variant());
    return true;
}

// GrimjawSkills.cast_r L3917
bool MysticHeroSkills::grimjaw_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        set_kit_value(h, "_omnislash_active", true);
        set_kit_value(h, "_omnislash_timer", 90);
        set_kit_value(h, "_omnislash_target", get_target(h));
        kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 2.5))), get_team(h), Variant(), "");
    } else {
        deal_aoe(h, all_units, all_towers, all_bases, 150, 2.0);
        set_kit_value(h, "_omnislash_active", true);
        set_kit_value(h, "_omnislash_timer", 90);
    }
    trigger_r(h, "grimjaw", 15, Variant());
    return true;
}

// KaizenSkills.init_state L3981
void MysticHeroSkills::kaizen_init_state(Object* h) {
    set_kit_value(h, "_q_stack", 0);
    set_kit_value(h, "_q_reset_timer", 0);
    set_kit_value(h, "_is_dashing", false);
    set_kit_value(h, "_dash_timer", 0);
    set_kit_value(h, "_wind_wall_timer", 0);
    set_kit_value(h, "_ulti_active", false);
    set_kit_value(h, "_ulti_timer", 0);
}

// KaizenSkills.update_timers L3992
void MysticHeroSkills::kaizen_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (((double)(get_kit_value(h, "_q_reset_timer")) > 0)) {
        set_kit_value(h, "_q_reset_timer", (int)get_kit_value(h, "_q_reset_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_q_reset_timer")) <= 0)) {
            set_kit_value(h, "_q_stack", 0);
        }
    }
    if (((double)(get_kit_value(h, "_dash_timer")) > 0)) {
        set_kit_value(h, "_dash_timer", (int)get_kit_value(h, "_dash_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_dash_timer")) <= 0)) {
            set_kit_value(h, "_is_dashing", false);
        }
    }
    if (((double)(get_kit_value(h, "_wind_wall_timer")) > 0)) {
        set_kit_value(h, "_wind_wall_timer", (int)get_kit_value(h, "_wind_wall_timer") - (int)(1));
    }
    if (((double)(get_kit_value(h, "_ulti_timer")) > 0)) {
        set_kit_value(h, "_ulti_timer", (int)get_kit_value(h, "_ulti_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_ulti_timer")) <= 0)) {
            set_kit_value(h, "_ulti_active", false);
        }
    }
}

// KaizenSkills.cast_q L4022
bool MysticHeroSkills::kaizen_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_q_reset_timer", 180);
    if (((int)(get_kit_value(h, "_q_stack")) == 0)) {
        kaizen_cast_steel_wind(h, all_units, all_towers, all_bases);
        set_kit_value(h, "_q_stack", 1);
    } else {
        kaizen_cast_dash_strike(h, all_units, all_towers, all_bases);
        set_kit_value(h, "_q_stack", 0);
    }
    trigger_q(h, "kaizen", 8, Variant());
    return true;
}

// KaizenSkills._cast_steel_wind L4048
void MysticHeroSkills::kaizen_cast_steel_wind(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant skill_range;

    skill_range = get_skill_data(h)["skill_range"];
    deal_aoe(h, all_units, all_towers, all_bases, skill_range, 1.0);
}

// KaizenSkills._cast_dash_strike L4056
void MysticHeroSkills::kaizen_cast_dash_strike(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant dx;
    Variant dy;

    if (!(get_target(h))) {
        return;
    }
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) > 0)) {
        set_global_pos_x(h, (get_global_pos_x(h)) + (((double)(dx) * 0.7)));
        set_global_pos_y(h, (get_global_pos_y(h)) + (((double)(dy) * 0.7)));
        set_kit_value(h, "_is_dashing", true);
        set_kit_value(h, "_dash_timer", 15);
        deal_aoe(h, all_units, all_towers, all_bases, 80, 1.5);
    }
}

// KaizenSkills.cast_w L4085
bool MysticHeroSkills::kaizen_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    set_kit_value(h, "_wind_wall_timer", 180);
    trigger_w(h, "kaizen", 5, Variant());
    return true;
}

// KaizenSkills.cast_e L4098
bool MysticHeroSkills::kaizen_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    deal_aoe(h, all_units, all_towers, all_bases, 100, 1.0);
    trigger_e(h, "kaizen", 6, Variant());
    return true;
}

// KaizenSkills.cast_r L4121
bool MysticHeroSkills::kaizen_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_ulti_active", true);
    set_kit_value(h, "_ulti_timer", 90);
    deal_aoe(h, all_units, all_towers, all_bases, 150, 2.0);
    trigger_r(h, "kaizen", 15, Variant());
    return true;
}

// SylaraSkills.init_state L4173
void MysticHeroSkills::sylara_init_state(Object* h) {
    set_kit_value(h, "_focus_fire_active", false);
    set_kit_value(h, "_focus_fire_timer", 0);
    set_kit_value(h, "_windrun_active", false);
    set_kit_value(h, "_windrun_timer", 0);
    set_kit_value(h, "_original_speed", get_speed_frames(h));
    set_kit_value(h, "_shackle_active", false);
    set_kit_value(h, "_shackle_timer", 0);
    set_kit_value(h, "_shackle_target", Variant());
    set_kit_value(h, "_powershot_charging", false);
    set_kit_value(h, "_powershot_timer", 0);
}

// SylaraSkills.update_timers L4195
void MysticHeroSkills::sylara_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant stats;

    if (((double)(get_kit_value(h, "_focus_fire_timer")) > 0)) {
        set_kit_value(h, "_focus_fire_timer", (int)get_kit_value(h, "_focus_fire_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_focus_fire_timer")) <= 0)) {
            set_kit_value(h, "_focus_fire_active", false);
            stats = kit_catalog_all(h)[get_hero_type(h)];
            set_attack_cooldown_frames(h, ((Dictionary)(stats))["attack_cooldown"]);
        }
    }
    if (((double)(get_kit_value(h, "_windrun_timer")) > 0)) {
        set_kit_value(h, "_windrun_timer", (int)get_kit_value(h, "_windrun_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_windrun_timer")) <= 0)) {
            set_kit_value(h, "_windrun_active", false);
            set_speed_frames(h, get_kit_value(h, "_original_speed"));
        }
    }
    if (((double)(get_kit_value(h, "_shackle_timer")) > 0)) {
        set_kit_value(h, "_shackle_timer", (int)get_kit_value(h, "_shackle_timer") - (int)(1));
        if ((get_kit_value(h, "_shackle_target")) && (kit_unit_alive(h, get_kit_value(h, "_shackle_target")))) {
            if (((int)(Math::fmod((double)(get_kit_value(h, "_shackle_timer")), (double)(15))) == 0)) {
                kit_hit(h, get_kit_value(h, "_shackle_target"), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.4))), get_team(h), Variant(), "");
                if (kit_has_atk_timer(h, get_kit_value(h, "_shackle_target"))) {
                    set_atk_timer_frames(h, get_kit_value(h, "_shackle_target"), 30);
                }
            }
        } else {
            set_kit_value(h, "_shackle_active", false);
            set_kit_value(h, "_shackle_target", Variant());
        }
        if (((double)(get_kit_value(h, "_shackle_timer")) <= 0)) {
            set_kit_value(h, "_shackle_active", false);
            set_kit_value(h, "_shackle_target", Variant());
        }
    }
    if (((double)(get_kit_value(h, "_powershot_timer")) > 0)) {
        set_kit_value(h, "_powershot_timer", (int)get_kit_value(h, "_powershot_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_powershot_timer")) <= 0)) {
            set_kit_value(h, "_powershot_charging", false);
            sylara_release_powershot(h, all_units, all_towers, all_bases);
        }
    }
}

// SylaraSkills.cast_q L4250
bool MysticHeroSkills::sylara_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant damage_falloff;
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant enemies;
    Variant ex;
    Variant ey;
    Variant hit_count;
    Variant perp_dist;
    Variant proj;
    Variant skill_range;

    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_focus_fire_active", true);
    set_kit_value(h, "_focus_fire_timer", 180);
    set_attack_cooldown_frames(h, MAX((double)(20), (double)((int64_t)(((double)(get_attack_cooldown_frames(h)) / 1.7)))));
    if (get_target(h)) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > 0)) {
            dx = (double)(dx) / (double)(dist);
            dy = (double)(dy) / (double)(dist);
            skill_range = get_skill_data(h)["skill_range"];
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            hit_count = 0;
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
                ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
                proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
                if ((0 < (double)(proj)) && ((double)(proj) < (double)(skill_range))) {
                    perp_dist = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
                    if (((double)(perp_dist) < 15)) {
                        damage_falloff = MAX((double)(0.5), (double)((1.0 - (double)(((double)(hit_count) * 0.15)))));
                        kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * (double)(damage_falloff)))), get_team(h), Variant(), "");
                        hit_count = (double)(hit_count) + (double)(1);
                    }
                }
            }
        }
    }
    trigger_q(h, "sylara", 8, Variant());
    return true;
}

// SylaraSkills.cast_w L4312
bool MysticHeroSkills::sylara_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    set_kit_value(h, "_windrun_active", true);
    set_kit_value(h, "_windrun_timer", 180);
    set_kit_value(h, "_original_speed", get_speed_frames(h));
    set_speed_frames(h, (get_speed_frames(h)) * (2.0));
    if (kit_has_hp(h, h)) {
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 30))));
    }
    trigger_w(h, "sylara", 5, Variant());
    return true;
}

// SylaraSkills.cast_e L4334
bool MysticHeroSkills::sylara_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Variant enemies;
    Variant nearest_dist;
    Variant shackle_range;
    Variant target;

    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    shackle_range = 200;
    target = Variant();
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dist = Vector2(((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= (double)(shackle_range))) {
            target = get_target(h);
        }
    }
    if (!(target)) {
        enemies = kit_enemies(h, all_units, all_towers, all_bases);
        nearest_dist = shackle_range;
        for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
            Variant __v_e = ((Array)(enemies))[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
            if (((double)(dist) < (double)(nearest_dist))) {
                target = e;
                nearest_dist = dist;
            }
        }
    }
    if (target) {
        set_kit_value(h, "_shackle_active", true);
        set_kit_value(h, "_shackle_timer", 150);
        set_kit_value(h, "_shackle_target", target);
        kit_hit(h, target, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.7))), get_team(h), Variant(), "");
        kit_lock(h, target, 45);
        trigger_e(h, "sylara", 6, Variant());
        return true;
    } else {
        return false;
    }
    return true;
}

// SylaraSkills.cast_r L4391
bool MysticHeroSkills::sylara_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_powershot_charging", true);
    set_kit_value(h, "_powershot_timer", 60);
    trigger_r(h, "sylara", 15, Variant());
    return true;
}

// SylaraSkills._release_powershot L4409
void MysticHeroSkills::sylara_release_powershot(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant arrow_angle;
    Variant arrow_dx;
    Variant arrow_dy;
    Variant arrow_i;
    Variant base_angle;
    Variant cone_angle;
    Variant damage;
    Variant dist;
    Variant distance_falloff;
    Variant dx;
    Variant dy;
    Variant e;
    Array enemies;
    Variant ex;
    Variant ey;
    Dictionary hit_enemies;
    Variant max_range;
    Variant num_arrows;
    Variant perp_dist;
    Variant proj;
    Variant spread;

    enemies = kit_enemies(h, all_units, all_towers, all_bases);
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > 0)) {
            dx = (double)(dx) / (double)(dist);
            dy = (double)(dy) / (double)(dist);
        } else {
            dx = get_facing(h);
            dy = 0;
        }
    } else {
        dx = get_facing(h);
        dy = 0;
    }
    num_arrows = 5;
    cone_angle = ((double)(Math_PI) / 6);
    max_range = 300;
    hit_enemies = Dictionary();
    for (int arrow_i=0; arrow_i< (int)(range_array(num_arrows).size()); ++arrow_i) {
        spread = ((double)(((double)(((double)(arrow_i) / (double)(((double)(num_arrows) - 1)))) - 0.5)) * (double)(cone_angle));
        base_angle = Math::atan2((double)(dy), (double)(dx));
        arrow_angle = ((double)(base_angle) + (double)(spread));
        arrow_dx = Math::cos((double)(arrow_angle));
        arrow_dy = Math::sin((double)(arrow_angle));
        for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
            Variant __v_e = ((Array)(enemies))[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if (hit_enemies.has(e)) {
                continue;
            }
            ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
            ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
            proj = ((double)(((double)(ex) * (double)(arrow_dx))) + (double)(((double)(ey) * (double)(arrow_dy))));
            if ((0 < (double)(proj)) && ((double)(proj) < (double)(max_range))) {
                perp_dist = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(arrow_dy))))) + (double)(((double)(ey) * (double)(arrow_dx))))));
                if (((double)(perp_dist) < 20)) {
                    distance_falloff = MAX((double)(0.6), (double)((1.0 - (double)(((double)(((double)(proj) / (double)(max_range))) * 0.4)))));
                    damage = (int64_t)(((double)(((double)(kit_skill_damage(h)) * 1.0)) * (double)(distance_falloff)));
                    kit_hit(h, e, (int)(damage), get_team(h), Variant(), "");
                    hit_enemies[Variant(e)] = true;
                    kit_skill_proj(h, e, 13.0);
                }
            }
        }
    }
}

// ThorneSkills.init_state L4493
void MysticHeroSkills::thorne_init_state(Object* h) {
    set_kit_value(h, "_viscous_nose_active", false);
    set_kit_value(h, "_viscous_nose_timer", 0);
    set_kit_value(h, "_bristleback_active", false);
    set_kit_value(h, "_bristleback_timer", 0);
    set_kit_value(h, "_spraying_quills", false);
    set_kit_value(h, "_spray_timer", 0);
    set_kit_value(h, "_warpath_active", false);
    set_kit_value(h, "_warpath_timer", 0);
    set_kit_value(h, "_original_damage", get_damage(h));
    set_kit_value(h, "_original_attack_cd", get_attack_cooldown_frames(h));
    set_kit_value(h, "_fortify_active", false);
    set_kit_value(h, "_fortify_timer", 0);
    set_kit_value(h, "_holy_shield_active", false);
    set_kit_value(h, "_holy_shield_timer", 0);
}

// ThorneSkills.update_timers L4521
void MysticHeroSkills::thorne_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant _lvl;

    if (((double)(get_kit_value(h, "_viscous_nose_timer")) > 0)) {
        set_kit_value(h, "_viscous_nose_timer", (int)get_kit_value(h, "_viscous_nose_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_viscous_nose_timer")) <= 0)) {
            set_kit_value(h, "_viscous_nose_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_bristleback_timer")) > 0)) {
        set_kit_value(h, "_bristleback_timer", (int)get_kit_value(h, "_bristleback_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_bristleback_timer")) <= 0)) {
            set_kit_value(h, "_bristleback_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_spray_timer")) > 0)) {
        set_kit_value(h, "_spray_timer", (int)get_kit_value(h, "_spray_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_spray_timer")) <= 0)) {
            set_kit_value(h, "_spraying_quills", false);
        }
    }
    if (((double)(get_kit_value(h, "_warpath_timer")) > 0)) {
        set_kit_value(h, "_warpath_timer", (int)get_kit_value(h, "_warpath_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_warpath_timer")) <= 0)) {
            set_kit_value(h, "_warpath_active", false);
            _lvl = kit_hero_levels(h).get(Variant(get_level(h)), Variant());
            if (_lvl) {
                set_damage(h, (int64_t)(((double)(get_base_damage(h)) * (double)(((Dictionary)(_lvl))["dmg_mult"]))));
            }
            set_attack_cooldown_frames(h, get_kit_value(h, "_original_attack_cd"));
        }
    }
}

// ThorneSkills.cast_q L4563
bool MysticHeroSkills::thorne_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant angle_diff;
    Variant cone_length;
    Variant cone_width;
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Array enemies;
    Variant enemy_angle;
    Variant facing_angle;

    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_viscous_nose_active", true);
    set_kit_value(h, "_viscous_nose_timer", 30);
    cone_length = 60;
    cone_width = ((double)(Math_PI) / 3);
    enemies = kit_enemies(h, all_units, all_towers, all_bases);
    for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
        Variant __v_e = ((Array)(enemies))[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dx = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
        dy = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
        dist = Vector2(dx, dy).length();
        if (((double)(dist) > (double)(cone_length))) {
            continue;
        }
        enemy_angle = Math::atan2((double)(dy), (double)(dx));
        facing_angle = (((double)(get_facing(h)) > 0) ? 0 : Math_PI);
        angle_diff = Math::abs((double)(((double)(enemy_angle) - (double)(facing_angle))));
        if (((double)(angle_diff) > (double)(Math_PI))) {
            angle_diff = ((double)((2 * (double)(Math_PI))) - (double)(angle_diff));
        }
        if (((double)(angle_diff) < (double)(((double)(cone_width) / 2)))) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
            kit_slow(h, e, 0.4, 180);
        }
    }
    trigger_q(h, "thorne", 6, Variant());
    return true;
}

// ThorneSkills.cast_w L4612
bool MysticHeroSkills::thorne_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    set_kit_value(h, "_bristleback_active", true);
    set_kit_value(h, "_bristleback_timer", 240);
    deal_aoe(h, all_units, all_towers, all_bases, 60, 0.5);
    if (kit_has_hp(h, h)) {
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 20))));
    }
    trigger_w(h, "thorne", 5, Variant());
    return true;
}

// ThorneSkills.cast_e L4638
bool MysticHeroSkills::thorne_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_spraying_quills", true);
    set_kit_value(h, "_spray_timer", 30);
    deal_aoe(h, all_units, all_towers, all_bases, 100, 1.2);
    trigger_e(h, "thorne", 8, Variant());
    return true;
}

// ThorneSkills.cast_r L4666
bool MysticHeroSkills::thorne_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_warpath_active", true);
    set_kit_value(h, "_warpath_timer", 300);
    set_kit_value(h, "_original_damage", get_damage(h));
    set_kit_value(h, "_original_attack_cd", get_attack_cooldown_frames(h));
    set_damage(h, (int64_t)(((double)(get_damage(h)) * 1.5)));
    set_attack_cooldown_frames(h, MAX((double)(15), (double)((int64_t)(((double)(get_attack_cooldown_frames(h)) / 1.5)))));
    deal_aoe(h, all_units, all_towers, all_bases, 120, 1.5);
    if (kit_has_hp(h, h)) {
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 50))));
    }
    trigger_r(h, "thorne", 15, Variant());
    return true;
}

// VexSkills.init_state L4732
void MysticHeroSkills::vex_init_state(Object* h) {
    set_kit_value(h, "_sanity_eclipse_active", false);
    set_kit_value(h, "_sanity_eclipse_timer", 0);
    set_kit_value(h, "_astral_prison_active", false);
    set_kit_value(h, "_astral_prison_timer", 0);
    set_kit_value(h, "_astral_prison_target", Variant());
    set_kit_value(h, "_essence_flux_active", false);
    set_kit_value(h, "_essence_flux_timer", 0);
}

// VexSkills.update_timers L4751
void MysticHeroSkills::vex_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Variant enemies;

    if (((double)(get_kit_value(h, "_sanity_eclipse_timer")) > 0)) {
        set_kit_value(h, "_sanity_eclipse_timer", (int)get_kit_value(h, "_sanity_eclipse_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "_sanity_eclipse_timer")), (double)(20))) == 0)) {
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
                if ((30 < (double)(dist)) && ((double)(dist) <= 55)) {
                    kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.4))), get_team(h), h, "");
                }
            }
        }
        if (((double)(get_kit_value(h, "_sanity_eclipse_timer")) <= 0)) {
            set_kit_value(h, "_sanity_eclipse_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_astral_prison_timer")) > 0)) {
        set_kit_value(h, "_astral_prison_timer", (int)get_kit_value(h, "_astral_prison_timer") - (int)(1));
        if ((get_kit_value(h, "_astral_prison_target")) && (kit_unit_alive(h, get_kit_value(h, "_astral_prison_target")))) {
            kit_lock(h, get_kit_value(h, "_astral_prison_target"), 15);
            if (((int)(Math::fmod((double)(get_kit_value(h, "_astral_prison_timer")), (double)(10))) == 0)) {
                kit_hit(h, get_kit_value(h, "_astral_prison_target"), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.3))), get_team(h), h, "");
            }
        } else {
            set_kit_value(h, "_astral_prison_active", false);
            set_kit_value(h, "_astral_prison_target", Variant());
        }
        if (((double)(get_kit_value(h, "_astral_prison_timer")) <= 0)) {
            set_kit_value(h, "_astral_prison_active", false);
            set_kit_value(h, "_astral_prison_target", Variant());
        }
    }
    if (((double)(get_kit_value(h, "_essence_flux_timer")) > 0)) {
        set_kit_value(h, "_essence_flux_timer", (int)get_kit_value(h, "_essence_flux_timer") - (int)(1));
        if (((double)(get_kit_value(h, "_essence_flux_timer")) <= 0)) {
            set_kit_value(h, "_essence_flux_active", false);
        }
    }
}

// VexSkills.cast_q L4801
bool MysticHeroSkills::vex_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant dx;
    Variant dy;
    Variant e;
    Variant enemies;
    Variant ex;
    Variant ey;
    Variant perp_dist;
    Variant proj;

    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    if (!(get_target(h))) {
        return false;
    }
    if (kit_unit_alive(h, get_target(h))) {
        kit_skill_proj(h, get_target(h), 13.0);
    }
    kit_hit(h, get_target(h), (int)((int64_t)(((double)(kit_skill_damage(h)) * 1.2))), get_team(h), Variant(), "");
    dx = ((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h)));
    dy = ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)));
    dist = Vector2(dx, dy).length();
    if (((double)(dist) > 0)) {
        dx = (double)(dx) / (double)(dist);
        dy = (double)(dy) / (double)(dist);
        enemies = kit_enemies(h, all_units, all_towers, all_bases);
        for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
            Variant __v_e = ((Array)(enemies))[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            if ((e == get_target(h))) {
                continue;
            }
            ex = ((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h)));
            ey = ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)));
            proj = ((double)(((double)(ex) * (double)(dx))) + (double)(((double)(ey) * (double)(dy))));
            if ((0 < (double)(proj)) && ((double)(proj) < (double)(dist))) {
                perp_dist = Math::abs((double)(((double)(((double)(ex) * (double)(-((double)(dy))))) + (double)(((double)(ey) * (double)(dx))))));
                if (((double)(perp_dist) < 18)) {
                    kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.5))), get_team(h), Variant(), "");
                }
            }
        }
    }
    trigger_q(h, "vex", 8, Variant());
    return true;
}

// VexSkills.cast_w L4854
bool MysticHeroSkills::vex_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Array enemies;

    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_sanity_eclipse_active", true);
    set_kit_value(h, "_sanity_eclipse_timer", 180);
    enemies = kit_enemies(h, all_units, all_towers, all_bases);
    for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
        Variant __v_e = ((Array)(enemies))[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= 60)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
            kit_slow(h, e, 0.5, 180);
        }
    }
    trigger_w(h, "vex", 5, Variant());
    return true;
}

// VexSkills.cast_e L4886
bool MysticHeroSkills::vex_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Variant enemies;
    Variant nearest_dist;
    Variant prison_range;
    Variant target;

    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    target = Variant();
    prison_range = 200;
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dist = Vector2(((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= (double)(prison_range))) {
            target = get_target(h);
        }
    }
    if (!(target)) {
        enemies = kit_enemies(h, all_units, all_towers, all_bases);
        nearest_dist = prison_range;
        for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
            Variant __v_e = ((Array)(enemies))[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
            if (((double)(dist) < (double)(nearest_dist))) {
                target = e;
                nearest_dist = dist;
            }
        }
    }
    if (target) {
        set_kit_value(h, "_astral_prison_active", true);
        set_kit_value(h, "_astral_prison_timer", 150);
        set_kit_value(h, "_astral_prison_target", target);
        kit_skill_proj(h, target, 13.0);
        kit_hit(h, target, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.6))), get_team(h), Variant(), "");
        trigger_e(h, "vex", 6, Variant());
        return true;
    } else {
        return false;
    }
    return true;
}

// VexSkills.cast_r L4939
bool MysticHeroSkills::vex_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_essence_flux_active", true);
    set_kit_value(h, "_essence_flux_timer", 60);
    deal_aoe(h, all_units, all_towers, all_bases, 180, 2.5);
    trigger_r(h, "vex", 15, Variant());
    return true;
}

// ZephyrSkills.init_state L4992
void MysticHeroSkills::zephyr_init_state(Object* h) {
    set_kit_value(h, "_bramble_active", false);
    set_kit_value(h, "_bramble_timer", 0);
    set_kit_value(h, "_bramble_origin", Variant());
    set_kit_value(h, "_shadow_realm_active", false);
    set_kit_value(h, "_shadow_realm_timer", 0);
    set_kit_value(h, "_curse_active", false);
    set_kit_value(h, "_curse_timer", 0);
    set_kit_value(h, "_curse_target", Variant());
    set_kit_value(h, "_bedlam_active", false);
    set_kit_value(h, "_bedlam_timer", 0);
}

// ZephyrSkills.update_timers L5016
void MysticHeroSkills::zephyr_update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Variant enemies;
    Variant ox;
    Variant oy;

    if (((double)(get_kit_value(h, "_bramble_timer")) > 0)) {
        set_kit_value(h, "_bramble_timer", (int)get_kit_value(h, "_bramble_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "_bramble_timer")), (double)(20))) == 0)) {
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            ox = ((Array)(py_or(get_kit_value(h, "_bramble_origin"), make_array(get_global_pos_x(h), get_global_pos_y(h)))))[0];
            oy = ((Array)(py_or(get_kit_value(h, "_bramble_origin"), make_array(get_global_pos_x(h), get_global_pos_y(h)))))[1];
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                dist = Vector2(((double)(get_global_pos_x(e)) - (double)(ox)), ((double)(get_global_pos_y(e)) - (double)(oy))).length();
                if ((40 < (double)(dist)) && ((double)(dist) <= 60)) {
                    kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.3))), get_team(h), h, "");
                    kit_slow(h, e, 0.5, 60);
                }
            }
        }
        if (((double)(get_kit_value(h, "_bramble_timer")) <= 0)) {
            set_kit_value(h, "_bramble_active", false);
            set_kit_value(h, "_bramble_origin", Variant());
        }
    }
    if (((double)(get_kit_value(h, "_shadow_realm_timer")) > 0)) {
        set_kit_value(h, "_shadow_realm_timer", (int)get_kit_value(h, "_shadow_realm_timer") - (int)(1));
        if (((double)(get_hp(h)) < (double)(get_max_hp(h)))) {
            set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 2))));
        }
        if (((double)(get_kit_value(h, "_shadow_realm_timer")) <= 0)) {
            set_kit_value(h, "_shadow_realm_active", false);
        }
    }
    if (((double)(get_kit_value(h, "_curse_timer")) > 0)) {
        set_kit_value(h, "_curse_timer", (int)get_kit_value(h, "_curse_timer") - (int)(1));
        if ((get_kit_value(h, "_curse_target")) && (kit_unit_alive(h, get_kit_value(h, "_curse_target")))) {
            if (((int)(Math::fmod((double)(get_kit_value(h, "_curse_timer")), (double)(20))) == 0)) {
                kit_hit(h, get_kit_value(h, "_curse_target"), (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.35))), get_team(h), h, "");
            }
        } else {
            set_kit_value(h, "_curse_active", false);
            set_kit_value(h, "_curse_target", Variant());
        }
        if (((double)(get_kit_value(h, "_curse_timer")) <= 0)) {
            set_kit_value(h, "_curse_active", false);
            set_kit_value(h, "_curse_target", Variant());
        }
    }
    if (((double)(get_kit_value(h, "_bedlam_timer")) > 0)) {
        set_kit_value(h, "_bedlam_timer", (int)get_kit_value(h, "_bedlam_timer") - (int)(1));
        if (((int)(Math::fmod((double)(get_kit_value(h, "_bedlam_timer")), (double)(15))) == 0)) {
            enemies = kit_enemies(h, all_units, all_towers, all_bases);
            for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
                Variant __v_e = ((Array)(enemies))[__i];
                Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
                dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
                if (((double)(dist) <= 80)) {
                    kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.5))), get_team(h), h, "");
                }
            }
        }
        if (((double)(get_kit_value(h, "_bedlam_timer")) <= 0)) {
            set_kit_value(h, "_bedlam_active", false);
        }
    }
}

// ZephyrSkills.cast_q L5086
bool MysticHeroSkills::zephyr_cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant dist;
    Variant e;
    Array enemies;
    Variant ox;
    Variant oy;
    Variant target;

    if (!(get_skill_timer(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    target = acquire_target(h, all_units, all_towers, all_bases, Variant());
    if ((target == Variant())) {
        return false;
    }
    set_kit_value(h, "_bramble_origin", make_array((double)(get_global_pos_x(target)), (double)(get_global_pos_y(target))));
    set_kit_value(h, "_bramble_active", true);
    set_kit_value(h, "_bramble_timer", 240);
    ox = ((Array)(get_kit_value(h, "_bramble_origin")))[0];
    oy = ((Array)(get_kit_value(h, "_bramble_origin")))[1];
    enemies = kit_enemies(h, all_units, all_towers, all_bases);
    for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
        Variant __v_e = ((Array)(enemies))[__i];
        Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
        dist = Vector2(((double)(get_global_pos_x(e)) - (double)(ox)), ((double)(get_global_pos_y(e)) - (double)(oy))).length();
        if (((double)(dist) <= 60)) {
            kit_hit(h, e, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.8))), get_team(h), Variant(), "");
            kit_slow(h, e, 0.5, 180);
        }
    }
    trigger_q(h, "zephyr", 8, Variant());
    return true;
}

// ZephyrSkills.cast_w L5124
bool MysticHeroSkills::zephyr_cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_w_cooldown(h) <= 0)) {
        return false;
    }
    set_kit_value(h, "_shadow_realm_active", true);
    set_kit_value(h, "_shadow_realm_timer", 180);
    if (kit_has_hp(h, h)) {
        set_hp(h, MIN((double)(get_max_hp(h)), (double)(((double)(get_hp(h)) + 40))));
    }
    trigger_w(h, "zephyr", 5, Variant());
    return true;
}

// ZephyrSkills.cast_e L5144
bool MysticHeroSkills::zephyr_cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    Variant curse_range;
    Variant dist;
    Variant e;
    Variant enemies;
    Variant nearest_dist;
    Variant target;

    if (!(get_e_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    target = Variant();
    curse_range = 200;
    if ((get_target(h)) && (kit_unit_alive(h, get_target(h)))) {
        dist = Vector2(((double)(get_global_pos_x(get_target(h))) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(get_target(h))) - (double)(get_global_pos_y(h)))).length();
        if (((double)(dist) <= (double)(curse_range))) {
            target = get_target(h);
        }
    }
    if (!(target)) {
        enemies = kit_enemies(h, all_units, all_towers, all_bases);
        nearest_dist = curse_range;
        for (int __i=0; __i< (int)(((Array)(enemies)).size()); ++__i) {
            Variant __v_e = ((Array)(enemies))[__i];
            Object* e = nullptr; if (__v_e.get_type()==Variant::OBJECT) e = Object::cast_to<Object>(__v_e); if (!e) continue;
            dist = Vector2(((double)(get_global_pos_x(e)) - (double)(get_global_pos_x(h))), ((double)(get_global_pos_y(e)) - (double)(get_global_pos_y(h)))).length();
            if (((double)(dist) < (double)(nearest_dist))) {
                target = e;
                nearest_dist = dist;
            }
        }
    }
    if (target) {
        set_kit_value(h, "_curse_active", true);
        set_kit_value(h, "_curse_timer", 180);
        set_kit_value(h, "_curse_target", target);
        kit_hit(h, target, (int)((int64_t)(((double)(kit_skill_damage(h)) * 0.6))), get_team(h), Variant(), "");
        trigger_e(h, "zephyr", 6, Variant());
        return true;
    } else {
        return false;
    }
    return true;
}

// ZephyrSkills.cast_r L5197
bool MysticHeroSkills::zephyr_cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    if (!(get_r_cooldown(h) <= 0)) {
        return false;
    }
    if (!(has_target(h, all_units, all_towers, all_bases, Variant()))) {
        return false;
    }
    set_kit_value(h, "_bedlam_active", true);
    set_kit_value(h, "_bedlam_timer", 240);
    deal_aoe(h, all_units, all_towers, all_bases, 80, 1.8);
    trigger_r(h, "zephyr", 15, Variant());
    return true;
}

// boss generic helpers
void MysticHeroSkills::fallback_cast(Object* h, const Array& enemies, const String& skill_key) {
    set_active_skill(h, Variant(skill_key)); set_active_skill_timer(h, 40);
    double mult=1.0; if (skill_key=="q") mult=1.0; else if (skill_key=="w") mult=1.2; else if (skill_key=="e") mult=1.5; else if (skill_key=="r") mult=2.5;
    String school = get_dmg_school(h);
    if (skill_key=="q" || skill_key=="w") { Object* tgt=get_target(h); if (tgt && kit_unit_alive(h,tgt)) { int dmg=(int)((double)kit_skill_damage(h)*mult); kit_hit(h,tgt,dmg,get_team(h),h,school); } }
    else { double aoe_range = skill_key=="e" ? 150.0 : 200.0; for(int i=0;i<enemies.size();++i){ Variant vv=enemies[i]; if(vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if(!e) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); if(Vector2(dx,dy).length()<=aoe_range){ int dmg=(int)((double)kit_skill_damage(h)*mult); kit_hit(h,e,dmg,get_team(h),h,school); } } }
}

bool MysticHeroSkills::boss_generic(Object* h, const String& skill_key, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    // cooldown check
    if (skill_key=="q" && get_skill_timer(h)>0) return false;
    if (skill_key=="w" && get_w_cooldown(h)>0) return false;
    if (skill_key=="e" && get_e_cooldown(h)>0) return false;
    if (skill_key=="r" && get_r_cooldown(h)>0) return false;
    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);
    double sr = get_skill_range(h); if (sr==0) sr=100; double cast_range = MAX((int)sr, 140);
    Array nearby; for(int i=0;i<enemies.size();++i){ Variant vv=enemies[i]; if(vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if(!e) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); double d=Vector2(dx,dy).length(); if(d<=cast_range){ Array t; t.append(d); t.append(e); t.append(nearby.size()); nearby.append(t);} }
    if (nearby.size()==0) return false;
    // nearby.sort_custom(__by_pair0) di GDScript == Python nearby.sort(key=t[0])
    // yang STABIL: urutkan (dist, idx) dengan insertion sort — idx unik dan
    // naik, jadi hasilnya identik dengan sort stabil by-dist. (Sort tukar
    // pasangan ala bubble TIDAK stabil: musuh berjarak sama bisa tertukar,
    // target skill boss jadi beda dari pygame.)
    for (int i=1; i<nearby.size(); ++i) {
        Variant keyv = nearby[i]; Array ka = keyv; double kd = (double)ka[0]; int64_t ki = (int64_t)ka[2];
        int j = i - 1;
        while (j >= 0) {
            Array ja = nearby[j]; double jd = (double)ja[0]; int64_t ji = (int64_t)ja[2];
            if (!(kd < jd || (kd == jd && ki < ji))) break;
            nearby[j+1] = nearby[j]; --j;
        }
        nearby[j+1] = keyv;
    }
    Object* tgt=get_target(h); bool valid=false; if(tgt && kit_unit_alive(h,tgt)){ double dx=get_global_pos_x(tgt)-get_global_pos_x(h); double dy=get_global_pos_y(tgt)-get_global_pos_y(h); if(Vector2(dx,dy).length()<=cast_range) valid=true; }
    if(!valid){ Object* best = Object::cast_to<Object>(((Array)nearby[0])[1]); set_target(h, best); }
    // check recipe
    String ht = get_hero_type(h);
    bool has_recipe = false;
    // list of recipe types
    const char* recipes[] = {
        "abaddon",
        "aeralith",
        "akahime",
        "akashari",
        "alchemist",
        "ancient_apparition",
        "astraelion",
        "aurelion",
        "aurelix",
        "aurelyssa",
        "aurethzar",
        "aurex",
        "auroth",
        "azureth",
        "cryssalia",
        "drakar",
        "gornak",
        "gravewake",
        "ignirus",
        "ignis_drachorn",
        "kaeldris",
        "kaelthar",
        "kaelthorn",
        "kenshiro",
        "khazan",
        "krobellus",
        "krognarr",
        "kunkka",
        "leoric",
        "luminar",
        "malzareth",
        "morgath",
        "morkhaera",
        "morthraxis",
        "morvaenthir",
        "morvein",
        "naraka",
        "nazulmor",
        "nyxarath",
        "nyxareth",
        "nyxareva",
        "nyxthrael",
        "nyzrak",
        "pyraethis",
        "pyraklos",
        "raz",
        "seiryukong",
        "shirotaka",
        "solara",
        "solvanth",
        "solvarin",
        "sylvantheros",
        "syrentha",
        "thalakryon",
        "thalgryn",
        "thornvaegrim",
        "thorvak",
        "vaelindra",
        "vargrath",
        "velmyrth",
        "vhalzun",
        "vorenmarr",
        "vraskhan",
        "wiro",
        "xyrael",
        "yamako",
        nullptr
    };
    for(int i=0;recipes[i]!=nullptr;++i) if (ht==recipes[i]) { has_recipe=true; break; }
    if (!has_recipe) { fallback_cast(h, enemies, skill_key); if (skill_key=="q") trigger_q(h,"boss",10); else if (skill_key=="w") trigger_w(h,"boss",8); else if (skill_key=="e") trigger_e(h,"boss",8); else trigger_r(h,"boss",15); return true; }
    bool ok = registry_dispatch(h, skill_key, enemies); if (!ok) return false;
    if (skill_key=="q") trigger_q(h,"boss",10); else if (skill_key=="w") trigger_w(h,"boss",8); else if (skill_key=="e") trigger_e(h,"boss",8); else trigger_r(h,"boss",15); return true;
}

bool MysticHeroSkills::registry_dispatch(Object* h, const String& skill_key, const Array& enemies) {
    String ht = get_hero_type(h);
    if (ht=="abaddon") {
        if (skill_key=="q") { bosshero_cast_q_mist_coil(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aphotic_shield(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_darkness_gale(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_death_sever(h, enemies); return true; }
        return false;
    }
    if (ht=="aeralith") {
        if (skill_key=="q") { bosshero_cast_q_aeralith_tailwind(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aeralith_windblade(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aeralith_vacuum(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aeralith_skyrider(h, enemies); return true; }
        return false;
    }
    if (ht=="akahime") {
        if (skill_key=="q") { bosshero_cast_q_akahime_petalbarrage(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_akahime_soulscroll(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_akahime_shadow(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_akahime_higanbana(h, enemies); return true; }
        return false;
    }
    if (ht=="akashari") {
        if (skill_key=="q") { bosshero_cast_q_akashari_strike(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_akashari_blink(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_akashari_scream(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_akashari_sonic(h, enemies); return true; }
        return false;
    }
    if (ht=="alchemist") {
        if (skill_key=="q") { bosshero_cast_q_acid_spray(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_unstable_concoction(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_chemical_rage(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_greevils_greed(h, enemies); return true; }
        return false;
    }
    if (ht=="ancient_apparition") {
        if (skill_key=="q") { bosshero_cast_q_ice_vortex(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_chilling_touch(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_ice_blast(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_cold_feet(h, enemies); return true; }
        return false;
    }
    if (ht=="astraelion") {
        if (skill_key=="q") { bosshero_cast_q_astraelion_swordfall(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_astraelion_spiritblade(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_astraelion_forceescape(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_astraelion_zeroreturn(h, enemies); return true; }
        return false;
    }
    if (ht=="aurelion") {
        if (skill_key=="q") { bosshero_cast_q_aurelion_callcourage(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aurelion_guardianassault(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aurelion_kingscommand(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aurelion_kingssummon(h, enemies); return true; }
        return false;
    }
    if (ht=="aurelix") {
        if (skill_key=="q") { bosshero_cast_q_aurelix_timebomb(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aurelix_will(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aurelix_shockwave(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aurelix_transcend(h, enemies); return true; }
        return false;
    }
    if (ht=="aurelyssa") {
        if (skill_key=="q") { bosshero_cast_q_aurelyssa_whirlwind(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aurelyssa_sweep(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aurelyssa_wings(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aurelyssa_phantom(h, enemies); return true; }
        return false;
    }
    if (ht=="aurethzar") {
        if (skill_key=="q") { bosshero_cast_q_aurethzar_marksman(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aurethzar_piercing(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aurethzar_frost(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aurethzar_thunder(h, enemies); return true; }
        return false;
    }
    if (ht=="aurex") {
        if (skill_key=="q") { bosshero_cast_q_aurex_shieldcrash(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_aurex_voltblast(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_aurex_aegis(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_aurex_spin(h, enemies); return true; }
        return false;
    }
    if (ht=="auroth") {
        if (skill_key=="q") { bosshero_cast_q_auroth_ionicedge(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_auroth_ward(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_auroth_consecration(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_auroth_guardian(h, enemies); return true; }
        return false;
    }
    if (ht=="azureth") {
        if (skill_key=="q") { bosshero_cast_q_azureth_arcanebolt(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_azureth_concussive(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_azureth_ancientseal(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_azureth_mysticflare(h, enemies); return true; }
        return false;
    }
    if (ht=="cryssalia") {
        if (skill_key=="q") { bosshero_cast_q_cryssalia_frostshock(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_cryssalia_bitterfrost(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_cryssalia_frostbites(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_cryssalia_coldest(h, enemies); return true; }
        return false;
    }
    if (ht=="drakar") {
        if (skill_key=="q") { bosshero_cast_q_battle_hunger(h); return true; }
        if (skill_key=="w") { bosshero_cast_w_counter_helix(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_berserkers_call(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_culling_blade(h); return true; }
        return false;
    }
    if (ht=="gornak") {
        if (skill_key=="q") { bosshero_cast_q_mana_break(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_blink(h); return true; }
        if (skill_key=="e") { bosshero_cast_e_counterspell(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_mana_void(h, enemies); return true; }
        return false;
    }
    if (ht=="gravewake") {
        if (skill_key=="q") { bosshero_cast_q_gravewake_anchor(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_gravewake_tide(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_gravewake_shell(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_gravewake_ravage(h, enemies); return true; }
        return false;
    }
    if (ht=="ignirus") {
        if (skill_key=="q") { bosshero_cast_q_ignirus_searingtorrent(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_ignirus_flameshot(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_ignirus_burstfireball(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_ignirus_vengeance(h, enemies); return true; }
        return false;
    }
    if (ht=="ignis_drachorn") {
        if (skill_key=="q") { bosshero_cast_q_dragon_breath(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_dragon_tail(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_dragon_blood(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_elder_dragon_form(h, enemies); return true; }
        return false;
    }
    if (ht=="kaeldris") {
        if (skill_key=="q") { bosshero_cast_q_kaeldris_overwhelming(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_kaeldris_press(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_kaeldris_moment(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_kaeldris_duel(h, enemies); return true; }
        return false;
    }
    if (ht=="kaelthar") {
        if (skill_key=="q") { bosshero_cast_q_kaelthar_chargingfist(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_kaelthar_quake(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_kaelthar_fistcrack(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_kaelthar_fistbreak(h, enemies); return true; }
        return false;
    }
    if (ht=="kaelthorn") {
        if (skill_key=="q") { bosshero_cast_q_kaelthorn_bravestfighter(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_kaelthorn_justiceblade(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_kaelthorn_defendersassault(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_kaelthorn_chivalryfists(h, enemies); return true; }
        return false;
    }
    if (ht=="kenshiro") {
        if (skill_key=="q") { bosshero_cast_q_kenshiro_swiftslash(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_kenshiro_assault(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_kenshiro_gale(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_kenshiro_supremacy(h, enemies); return true; }
        return false;
    }
    if (ht=="khazan") {
        if (skill_key=="q") { bosshero_cast_q_khazan_chained(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_khazan_leap(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_khazan_spin(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_khazan_vanish(h, enemies); return true; }
        return false;
    }
    if (ht=="krobellus") {
        if (skill_key=="q") { bosshero_cast_q_krobellus_exorcism(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_krobellus_silence(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_krobellus_siphon(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_krobellus_crypt(h, enemies); return true; }
        return false;
    }
    if (ht=="krognarr") {
        if (skill_key=="q") { bosshero_cast_q_krognarr_strike(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_krognarr_seismic(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_krognarr_rampart(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_krognarr_eruption(h, enemies); return true; }
        return false;
    }
    if (ht=="kunkka") {
        if (skill_key=="q") { bosshero_cast_q_kunkka_tide(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_kunkka_xmark(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_kunkka_ghost(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_kunkka_torrent(h, enemies); return true; }
        return false;
    }
    if (ht=="leoric") {
        if (skill_key=="q") { bosshero_cast_q_leoric_fearlesscharge(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_leoric_sacredhammer(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_leoric_concealblast(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_leoric_immortality(h, enemies); return true; }
        return false;
    }
    if (ht=="luminar") {
        if (skill_key=="q") { bosshero_cast_q_luminar_illuminate(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_luminar_blindinglight(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_luminar_wisp(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_luminar_spiritform(h, enemies); return true; }
        return false;
    }
    if (ht=="malzareth") {
        if (skill_key=="q") { bosshero_cast_q_malzareth_disruption(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_malzareth_soul(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_malzareth_poison(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_malzareth_disillusion(h, enemies); return true; }
        return false;
    }
    if (ht=="morgath") {
        if (skill_key=="q") { bosshero_cast_q_spark_wraith(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_flux(h); return true; }
        if (skill_key=="e") { bosshero_cast_e_magnetic_field(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_tempest_double(h); return true; }
        return false;
    }
    if (ht=="morkhaera") {
        if (skill_key=="q") { bosshero_cast_q_morkhaera_spiritburst(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_morkhaera_airstrike(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_morkhaera_energyimpact(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_morkhaera_ethereal(h, enemies); return true; }
        return false;
    }
    if (ht=="morthraxis") {
        if (skill_key=="q") { bosshero_cast_q_morthraxis_batimpale(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_morthraxis_sanguine(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_morthraxis_phantommob(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_morthraxis_baleful(h, enemies); return true; }
        return false;
    }
    if (ht=="morvaenthir") {
        if (skill_key=="q") { bosshero_cast_q_morvaenthir_soulfragment(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_morvaenthir_spiritbind(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_morvaenthir_essence(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_morvaenthir_shadowrealm(h, enemies); return true; }
        return false;
    }
    if (ht=="morvein") {
        if (skill_key=="q") { bosshero_cast_q_morvein_puncture(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_morvein_violentstrike(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_morvein_spectralcharge(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_morvein_phantomform(h, enemies); return true; }
        return false;
    }
    if (ht=="naraka") {
        if (skill_key=="q") { bosshero_cast_q_naraka_chaos(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_naraka_shadowstep(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_naraka_hammer(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_naraka_execution(h, enemies); return true; }
        return false;
    }
    if (ht=="nazulmor") {
        if (skill_key=="q") { bosshero_cast_q_nazulmor_typhoon(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_nazulmor_aquashield(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_nazulmor_tidalrage(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_nazulmor_chaotic(h, enemies); return true; }
        return false;
    }
    if (ht=="nyxarath") {
        if (skill_key=="q") { bosshero_cast_q_nyxarath_shadowraze(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_nyxarath_necro(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_nyxarath_presence(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_nyxarath_requiem(h, enemies); return true; }
        return false;
    }
    if (ht=="nyxareth") {
        if (skill_key=="q") { bosshero_cast_q_nyxareth_starsplit(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_nyxareth_realworld(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_nyxareth_spacetime(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_nyxareth_astrorealm(h, enemies); return true; }
        return false;
    }
    if (ht=="nyxareva") {
        if (skill_key=="q") { bosshero_cast_q_nyxareva_darkslash(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_nyxareva_mortalwound(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_nyxareva_sacrifice(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_nyxareva_avatar(h, enemies); return true; }
        return false;
    }
    if (ht=="nyxthrael") {
        if (skill_key=="q") { bosshero_cast_q_nyxthrael_ambush(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_nyxthrael_nightfall(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_nyxthrael_darknightfall(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_nyxthrael_shadowbringer(h, enemies); return true; }
        return false;
    }
    if (ht=="nyzrak") {
        if (skill_key=="q") { bosshero_cast_q_arctic_burn(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_splinter_blast(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_winters_curse(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_cold_embrace(h, enemies); return true; }
        return false;
    }
    if (ht=="pyraethis") {
        if (skill_key=="q") { bosshero_cast_q_pyraethis_icarusdive(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_pyraethis_firespirits(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_pyraethis_sunray(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_pyraethis_supernova(h, enemies); return true; }
        return false;
    }
    if (ht=="pyraklos") {
        if (skill_key=="q") { bosshero_cast_q_pyraklos_spearmars(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_pyraklos_rebuke(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_pyraklos_bulwark(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_pyraklos_arena(h, enemies); return true; }
        return false;
    }
    if (ht=="raz") {
        if (skill_key=="q") { bosshero_cast_q_raz_overdrive(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_raz_searing(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_raz_surge(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_raz_gloom(h, enemies); return true; }
        return false;
    }
    if (ht=="seiryukong") {
        if (skill_key=="q") { bosshero_cast_q_seiryukong_boundless(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_seiryukong_treedance(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_seiryukong_jingusoldiers(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_seiryukong_wukong(h, enemies); return true; }
        return false;
    }
    if (ht=="shirotaka") {
        if (skill_key=="q") { bosshero_cast_q_shirotaka_hiraishin(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_shirotaka_waterboundary(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_shirotaka_shadowclones(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_shirotaka_paperbomb(h, enemies); return true; }
        return false;
    }
    if (ht=="solara") {
        if (skill_key=="q") { bosshero_cast_q_solara_starbreaker(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_solara_celestialhammer(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_solara_luminosity(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_solara_solarguardian(h, enemies); return true; }
        return false;
    }
    if (ht=="solvanth") {
        if (skill_key=="q") { bosshero_cast_q_solvanth_ringpunishment(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_solvanth_gloriouspathway(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_solvanth_laworder(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_solvanth_wrath(h, enemies); return true; }
        return false;
    }
    if (ht=="solvarin") {
        if (skill_key=="q") { bosshero_cast_q_solvarin_purification(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_solvarin_repel(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_solvarin_degen(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_solvarin_guardian(h, enemies); return true; }
        return false;
    }
    if (ht=="sylvantheros") {
        if (skill_key=="q") { bosshero_cast_q_sylvantheros_sprout(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_sylvantheros_teleport(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_sylvantheros_treants(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_sylvantheros_wrath(h, enemies); return true; }
        return false;
    }
    if (ht=="syrentha") {
        if (skill_key=="q") { bosshero_cast_q_syrentha_riptide(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_syrentha_song(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_syrentha_mirror(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_syrentha_siren(h, enemies); return true; }
        return false;
    }
    if (ht=="thalakryon") {
        if (skill_key=="q") { bosshero_cast_q_thalakryon_bolt(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_thalakryon_aquashield(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_thalakryon_tidalrage(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_thalakryon_metamorph(h, enemies); return true; }
        return false;
    }
    if (ht=="thalgryn") {
        if (skill_key=="q") { bosshero_cast_q_thalgryn_waveform(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_thalgryn_adaptive(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_thalgryn_morph(h); return true; }
        if (skill_key=="r") { bosshero_cast_r_thalgryn_replicate(h, enemies); return true; }
        return false;
    }
    if (ht=="thornvaegrim") {
        if (skill_key=="q") { bosshero_cast_q_thornvaegrim_bramble(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_thornvaegrim_twistedadvance(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_thornvaegrim_saplingthrow(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_thornvaegrim_grasp(h, enemies); return true; }
        return false;
    }
    if (ht=="thorvak") {
        if (skill_key=="q") { bosshero_cast_q_thorvak_seed(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_thorvak_natureswrath(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_thorvak_vengeance(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_thorvak_dryad(h, enemies); return true; }
        return false;
    }
    if (ht=="vaelindra") {
        if (skill_key=="q") { bosshero_cast_q_vaelindra_energywave(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_vaelindra_spacering(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_vaelindra_violetrequiem(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_vaelindra_realm(h, enemies); return true; }
        return false;
    }
    if (ht=="vargrath") {
        if (skill_key=="q") { bosshero_cast_q_vargrath_bloodthirst(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_vargrath_charge(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_vargrath_devilstrike(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_vargrath_souldom(h, enemies); return true; }
        return false;
    }
    if (ht=="velmyrth") {
        if (skill_key=="q") { bosshero_cast_q_velmyrth_dagger(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_velmyrth_strike(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_velmyrth_blur(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_velmyrth_coup(h, enemies); return true; }
        return false;
    }
    if (ht=="vhalzun") {
        if (skill_key=="q") { bosshero_cast_q_vhalzun_death_pulse(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_vhalzun_heartstopper(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_vhalzun_reapers_scythe(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_vhalzun_ghost_shroud(h, enemies); return true; }
        return false;
    }
    if (ht=="vorenmarr") {
        if (skill_key=="q") { bosshero_cast_q_vorenmarr_bonds(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_vorenmarr_power(h); return true; }
        if (skill_key=="e") { bosshero_cast_e_vorenmarr_upheaval(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_vorenmarr_golem(h, enemies); return true; }
        return false;
    }
    if (ht=="vraskhan") {
        if (skill_key=="q") { bosshero_cast_q_vraskhan_thorned(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_vraskhan_leap(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_vraskhan_deathslash(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_vraskhan_omni(h, enemies); return true; }
        return false;
    }
    if (ht=="wiro") {
        if (skill_key=="q") { bosshero_cast_q_wiro_windcut(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_wiro_whirl(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_wiro_dash(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_wiro_typhoon(h, enemies); return true; }
        return false;
    }
    if (ht=="xyrael") {
        if (skill_key=="q") { bosshero_cast_q_xyrael_finch(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_xyrael_defiant(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_xyrael_tempest(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_xyrael_lightness(h, enemies); return true; }
        return false;
    }
    if (ht=="yamako") {
        if (skill_key=="q") { bosshero_cast_q_yamako_deepforest(h, enemies); return true; }
        if (skill_key=="w") { bosshero_cast_w_yamako_woodcreation(h, enemies); return true; }
        if (skill_key=="e") { bosshero_cast_e_yamako_woodgolem(h, enemies); return true; }
        if (skill_key=="r") { bosshero_cast_r_yamako_kannon(h, enemies); return true; }
        return false;
    }
    return false;
}

void MysticHeroSkills::init_state(Object* h) {
    String kind = hero_kind(h);
    // reset kit
    set_kit(h, Dictionary());
    if (kind=="grimjaw") grimjaw_init_state(h);
    else if (kind=="kaizen") kaizen_init_state(h);
    else if (kind=="sylara") sylara_init_state(h);
    else if (kind=="thorne") thorne_init_state(h);
    else if (kind=="vex") vex_init_state(h);
    else if (kind=="zephyr") zephyr_init_state(h);
    else bosshero_init_state(h);
}
void MysticHeroSkills::update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    String kind = hero_kind(h);
    if (kind=="grimjaw") grimjaw_update_timers(h, all_units, all_towers, all_bases);
    else if (kind=="kaizen") kaizen_update_timers(h, all_units, all_towers, all_bases);
    else if (kind=="sylara") sylara_update_timers(h, all_units, all_towers, all_bases);
    else if (kind=="thorne") thorne_update_timers(h, all_units, all_towers, all_bases);
    else if (kind=="vex") vex_update_timers(h, all_units, all_towers, all_bases);
    else if (kind=="zephyr") zephyr_update_timers(h, all_units, all_towers, all_bases);
    else bosshero_update_timers(h, all_units, all_towers, all_bases);
}
bool MysticHeroSkills::cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    String kind = hero_kind(h);
    if (kind=="grimjaw") return grimjaw_cast_q(h, all_units, all_towers, all_bases);
    if (kind=="kaizen") return kaizen_cast_q(h, all_units, all_towers, all_bases);
    if (kind=="sylara") return sylara_cast_q(h, all_units, all_towers, all_bases);
    if (kind=="thorne") return thorne_cast_q(h, all_units, all_towers, all_bases);
    if (kind=="vex") return vex_cast_q(h, all_units, all_towers, all_bases);
    if (kind=="zephyr") return zephyr_cast_q(h, all_units, all_towers, all_bases);
    return boss_generic(h, "q", all_units, all_towers, all_bases);
}
bool MysticHeroSkills::cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    String kind = hero_kind(h);
    if (kind=="grimjaw") return grimjaw_cast_w(h, all_units, all_towers, all_bases);
    if (kind=="kaizen") return kaizen_cast_w(h, all_units, all_towers, all_bases);
    if (kind=="sylara") return sylara_cast_w(h, all_units, all_towers, all_bases);
    if (kind=="thorne") return thorne_cast_w(h, all_units, all_towers, all_bases);
    if (kind=="vex") return vex_cast_w(h, all_units, all_towers, all_bases);
    if (kind=="zephyr") return zephyr_cast_w(h, all_units, all_towers, all_bases);
    return boss_generic(h, "w", all_units, all_towers, all_bases);
}
bool MysticHeroSkills::cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    String kind = hero_kind(h);
    if (kind=="grimjaw") return grimjaw_cast_e(h, all_units, all_towers, all_bases);
    if (kind=="kaizen") return kaizen_cast_e(h, all_units, all_towers, all_bases);
    if (kind=="sylara") return sylara_cast_e(h, all_units, all_towers, all_bases);
    if (kind=="thorne") return thorne_cast_e(h, all_units, all_towers, all_bases);
    if (kind=="vex") return vex_cast_e(h, all_units, all_towers, all_bases);
    if (kind=="zephyr") return zephyr_cast_e(h, all_units, all_towers, all_bases);
    return boss_generic(h, "e", all_units, all_towers, all_bases);
}
bool MysticHeroSkills::cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {
    String kind = hero_kind(h);
    if (kind=="grimjaw") return grimjaw_cast_r(h, all_units, all_towers, all_bases);
    if (kind=="kaizen") return kaizen_cast_r(h, all_units, all_towers, all_bases);
    if (kind=="sylara") return sylara_cast_r(h, all_units, all_towers, all_bases);
    if (kind=="thorne") return thorne_cast_r(h, all_units, all_towers, all_bases);
    if (kind=="vex") return vex_cast_r(h, all_units, all_towers, all_bases);
    if (kind=="zephyr") return zephyr_cast_r(h, all_units, all_towers, all_bases);
    return boss_generic(h, "r", all_units, all_towers, all_bases);
}

bool MysticHeroSkills::by_pair0(Variant a, Variant b) {
    Array aa = a; Array bb = b;
    if (aa.size() < 3 || bb.size() < 3) { double av = aa.size() > 0 ? (double)aa[0] : 0.0; double bv = bb.size() > 0 ? (double)bb[0] : 0.0; return av < bv; }
    double ad = (double)aa[0]; double bd = (double)bb[0];
    if (ad == bd) return (int64_t)aa[2] < (int64_t)bb[2];
    return ad < bd;
}
bool MysticHeroSkills::__by_pair0(Variant a, Variant b) { return by_pair0(a,b); }

void MysticHeroSkills::_bind_methods() {
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("init_state", "hero"), &MysticHeroSkills::init_state);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("update_timers", "hero", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::update_timers);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("cast_q", "hero", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::cast_q);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("cast_w", "hero", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::cast_w);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("cast_e", "hero", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::cast_e);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("cast_r", "hero", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::cast_r);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("hero_kind", "hero"), &MysticHeroSkills::hero_kind);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("skill_range", "hero", "fallback"), &MysticHeroSkills::skill_range, DEFVAL(200.0));
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("has_target", "hero", "all_units", "all_towers", "all_bases", "range_val"), &MysticHeroSkills::has_target, DEFVAL(Variant()));
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("visual_duration", "hero_type", "key"), &MysticHeroSkills::visual_duration);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("boss_generic", "hero", "skill_key", "all_units", "all_towers", "all_bases"), &MysticHeroSkills::boss_generic);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("by_pair0", "a", "b"), &MysticHeroSkills::by_pair0);
    ClassDB::bind_static_method("MysticHeroSkills", D_METHOD("__by_pair0", "a", "b"), &MysticHeroSkills::__by_pair0);
}