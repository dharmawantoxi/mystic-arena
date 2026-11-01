class_name AppState
extends RefCounted

enum Kind { SPLASH, MENU, GAME, PAUSE }

const NAMES := {
	Kind.SPLASH: "splash",
	Kind.MENU: "menu",
	Kind.GAME: "game",
	Kind.PAUSE: "pause",
}
const TRANSITIONS := {
	Kind.SPLASH: [Kind.MENU],
	Kind.MENU: [Kind.GAME],
	Kind.GAME: [Kind.PAUSE, Kind.MENU],
	Kind.PAUSE: [Kind.GAME, Kind.MENU],
}

var current: Kind = Kind.SPLASH


func can_transition(next: Kind) -> bool:
	return next in TRANSITIONS[current]


func transition(next: Kind) -> bool:
	if not can_transition(next):
		return false
	current = next
	return true


func label() -> String:
	return NAMES[current]


func simulates_game() -> bool:
	return current == Kind.GAME
