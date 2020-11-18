export let PUNCTUATION_REGEX;

const PUNCTUATION = "" +
"’'" +       // apostrophe
"()[]{}<>" + // brackets
":" +        // colon
"," +        // comma
"‒–—―" +     // dashes
"…" +        // ellipsis
"!" +        // exclamation mark
"." +        // full stop/period
"«»" +       // guillemets
"-‐" +       // hyphen
"?" +        // question mark
"‘’“”" +     // quotation marks
";" +        // semicolon
"/" +        // slash/stroke
"⁄" +        // solidus
"␠" +        // space?
"·" +        // interpunct
"&" +        // ampersand
"@" +        // at sign
"*" +        // asterisk
"\\" +       // backslash
"•" +        // bullet
"^" +        // caret
"¤¢$€£¥₩₪" + // currency
"†‡" +       // dagger
"°" +        // degree
"¡" +        // inverted exclamation point
"¿" +        // inverted question mark
"¬" +        // negation
"#" +        // number sign (hashtag)
"№" +        // numero sign ()
"%‰‱" +      // percent and related signs
"¶" +        // pilcrow
"′" +        // prime
"§" +        // section sign
"~" +        // tilde/swung dash
"¨" +        // umlaut/diaeresis
"_" +        // underscore/understrike
"|¦" +       // vertical/pipe/broken bar
"⁂" +        // asterism
"☞" +        // index/fist
"∴" +        // therefore sign
"‽" +        // interrobang
"+=±≤≥≠º≈∞•√∫Ω∂ƒ" +        // math
"©" +        // copyright sign
"※"          // reference mark

// escape punctuation characters for regular expression
PUNCTUATION_REGEX = `[${PUNCTUATION.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&")}]`;
