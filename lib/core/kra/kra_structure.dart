/// Canonical FacultyLink KRA hierarchy for Web and Mobile frontends.
abstract final class KraStructure {
  static const kraI = 'KRA I';
  static const kraII = 'KRA II';
  static const kraIII = 'KRA III';
  static const kraIV = 'KRA IV';

  static const kraOptions = [kraI, kraII, kraIII, kraIV];

  static const Map<String, List<String>> criteriaLetters = {
    kraI: ['A', 'B', 'C'],
    kraII: ['A', 'B', 'C'],
    kraIII: ['A', 'B', 'C', 'D'],
    kraIV: ['A', 'B', 'C', 'D'],
  };

  static const Map<String, String> kraTitles = {
    kraI: 'KRA I — Instruction',
    kraII: 'KRA II — Research and Innovation',
    kraIII: 'KRA III — Extension or Community Services',
    kraIV: 'KRA IV — Professional Development',
  };

  static List<String> lettersFor(String? kra) {
    if (kra == null) return const [];
    return criteriaLetters[kra] ?? const [];
  }

  static bool isValidPair(String? kra, String? letter) {
    if (kra == null || letter == null) return false;
    return lettersFor(kra).contains(letter);
  }

  /// Parses dropdown values like `A — Teaching` to letter `A`.
  static String criterionLetter(String value) {
    final trimmed = value.trim();
    if (trimmed.length == 1) return trimmed;
    final dash = trimmed.indexOf('—');
    if (dash > 0) return trimmed.substring(0, dash).trim();
    final space = trimmed.indexOf(' ');
    if (space > 0) return trimmed.substring(0, space).trim();
    return trimmed;
  }
}
