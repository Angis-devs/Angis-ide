"""Multilingual support for Angis programming language."""


class LangPack:
    def __init__(
        self, code: str, name: str,
        print_words: set[str],
        set_words: set[str],
        math_words: set[str],
        app_words: set[str],
        game_words: set[str],
        file_words: set[str],
        to_prep: set[str],
        equal_prep: set[str],
        for_prep: set[str],
        in_prep: set[str],
        as_prep: set[str],
        if_word: str,
        else_word: str,
        and_word: str,
        or_word: str,
        not_word: str,
        true_words: set[str],
        false_words: set[str],
        on_word: str,
        off_word: str,
        switch_word: str,
        match_word: str,
        case_word: str,
        when_word: str,
        default_word: str,
        otherwise_word: str,
        define_word: str,
        function_word: str,
        return_word: str,
        call_word: str,
        blueprint_word: str,
        create_word: str,
        named_word: str,
        method_word: str,
        phrase_word: str,
        command_word: str,
        means_word: str,
        teaching_words: set[str],
        repeat_word: str,
        times_word: str,
        while_word: str,
        for_each_words: set[str],
        collect_word: str,
        get_word: str,
        lambda_word: str,
        arrow_word: str,
        fn_word: str,
        into_prep: str,
        try_word: str,
        except_word: str,
        catch_word: str,
        finally_word: str,
        with_word: str,
        async_word: str,
        spawn_word: str,
        background_word: str,
        await_word: str,
        decorator_char: str,
        yes_words: set[str],
        no_words: set[str],
        import_word: str,
        python_word: str,
        include_word: str,
        library_word: str,
        pack_word: str,
        use_word: str,
        show_word: str,
        say_word: str,
        display_word: str,
        tell_word: str,
        ask_word: str,
        input_word: str,
        prompt_word: str,
        read_word: str,
        raise_word: str,
        error_word: str,
        assert_word: str,
        debug_word: str,
        all_word: str,
        language_word: str,
        true_word: str,
        false_word: str,
    ):
        self.code = code
        self.name = name
        self._p = print_words
        self._s = set_words
        self._m = math_words
        self._a = app_words
        self._g = game_words
        self._f = file_words
        self.to = to_prep
        self.equal = equal_prep
        self.for_p = for_prep
        self.in_p = in_prep
        self.as_p = as_prep
        self.if_w = if_word
        self.else_w = else_word
        self.and_w = and_word
        self.or_w = or_word
        self.not_w = not_word
        self.true = true_words
        self.false = false_words
        self.on = on_word
        self.off = off_word
        self.switch = switch_word
        self.match = match_word
        self.case = case_word
        self.when = when_word
        self.default = default_word
        self.otherwise = otherwise_word
        self.define = define_word
        self.function = function_word
        self.return_w = return_word
        self.call = call_word
        self.blueprint = blueprint_word
        self.create = create_word
        self.named = named_word
        self.method = method_word
        self.phrase = phrase_word
        self.command = command_word
        self.means = means_word
        self.teaching = teaching_words
        self.repeat = repeat_word
        self.times = times_word
        self.while_w = while_word
        self.for_each = for_each_words
        self.collect = collect_word
        self.get = get_word
        self.lambda_w = lambda_word
        self.arrow = arrow_word
        self.fn = fn_word
        self.into = into_prep
        self.try_w = try_word
        self.except_w = except_word
        self.catch = catch_word
        self.finally_w = finally_word
        self.with_w = with_word
        self.async_w = async_word
        self.spawn = spawn_word
        self.background = background_word
        self.await_w = await_word
        self.decorator = decorator_char
        self.yes = yes_words
        self.no = no_words
        self.import_w = import_word
        self.python = python_word
        self.include = include_word
        self.library = library_word
        self.pack = pack_word
        self.use = use_word
        self.show = show_word
        self.say = say_word
        self.display = display_word
        self.tell = tell_word
        self.ask = ask_word
        self.input = input_word
        self.prompt = prompt_word
        self.read = read_word
        self.raise_w = raise_word
        self.error_w = error_word
        self.assert_w = assert_word
        self.debug = debug_word
        self.all_w = all_word
        self.language = language_word
        self.true_word = true_word
        self.false_word = false_word
        self._ui: dict[str, str] = {}

    def ui(self, key: str) -> str:
        return self._ui.get(key, key)

    def print_w(self) -> str:
        return _group(self._p)

    def set_w(self) -> str:
        return _group(self._s)

    def math_w(self) -> str:
        return _group(self._m)

    def app_w(self) -> str:
        return _group(self._a)

    def game_w(self) -> str:
        return _group(self._g)

    def file_w(self) -> str:
        return _group(self._f)

    def to_w(self) -> str:
        return _group(self.to)

    def equal_w(self) -> str:
        return _group(self.equal)

    def for_w(self) -> str:
        return _group(self.for_p)

    def in_w(self) -> str:
        return _group(self.in_p)

    def as_w(self) -> str:
        return _group(self.as_p)

    def true_w(self) -> str:
        return _group(self.true)

    def false_w(self) -> str:
        return _group(self.false)

    def yes_w(self) -> str:
        return _group(self.yes)

    def no_w(self) -> str:
        return _group(self.no)

    def for_each_w(self) -> str:
        return _group(self.for_each)

    def teaching_w(self) -> str:
        return _group(self.teaching)

    def create_w(self) -> str:
        return _group(self._a | {self.create})


def _group(words: set[str]) -> str:
    return "(?:" + "|".join(sorted(words, key=len, reverse=True)) + ")"


_EN_UI = {
    "open": "Open",
    "save": "Save",
    "save_as": "Save As",
    "cut": "Cut",
    "copy": "Copy",
    "paste": "Paste",
    "run": "Run",
    "close_tab": "Close Tab",
    "editor": "Editor",
    "output": "Output",
    "errors": "Errors",
    "select_all": "Select All",
    "settings": "Settings",
    "language": "Language",
    "window_title": "Angis IDE",
    "untitled": "untitled",
    "angis_files": "Angis files",
    "all_files": "All files",
    "text_files": "Text files",
    "set_language": "Set Language",
    "choose_language": "Choose IDE language:",
    "apply": "Apply",
    "cancel": "Cancel",
    "loading": "Loading...",
    "game_over": "Game Over",
    "canvas_ready": "Canvas ready",
    "use_wasd": "Use WASD or arrow keys to move",
    "score": "Score",
    "click_or_space": "Click or press Space to flap",
    "click_restart": "Click or press Space to restart",
}

_SP_UI = {
    "open": "Abrir",
    "save": "Guardar",
    "save_as": "Guardar Como",
    "cut": "Cortar",
    "copy": "Copiar",
    "paste": "Pegar",
    "run": "Ejecutar",
    "close_tab": "Cerrar Pestaña",
    "editor": "Editor",
    "output": "Salida",
    "errors": "Errores",
    "select_all": "Seleccionar Todo",
    "settings": "Configuración",
    "language": "Idioma",
    "window_title": "IDE de Angis",
    "untitled": "sin título",
    "angis_files": "Archivos Angis",
    "all_files": "Todos los archivos",
    "text_files": "Archivos de texto",
    "set_language": "Establecer Idioma",
    "choose_language": "Elige el idioma del IDE:",
    "apply": "Aplicar",
    "cancel": "Cancelar",
    "loading": "Cargando...",
    "game_over": "Juego Terminado",
    "canvas_ready": "Lienzo listo",
    "use_wasd": "Usa WASD o flechas para moverte",
    "score": "Puntuación",
    "click_or_space": "Haz clic o presiona Espacio para aletear",
    "click_restart": "Haz clic o presiona Espacio para reiniciar",
}

_FR_UI = {
    "open": "Ouvrir",
    "save": "Enregistrer",
    "save_as": "Enregistrer Sous",
    "cut": "Couper",
    "copy": "Copier",
    "paste": "Coller",
    "run": "Exécuter",
    "close_tab": "Fermer l'Onglet",
    "editor": "Éditeur",
    "output": "Sortie",
    "errors": "Erreurs",
    "select_all": "Tout Sélectionner",
    "settings": "Paramètres",
    "language": "Langue",
    "window_title": "IDE Angis",
    "untitled": "sans titre",
    "angis_files": "Fichiers Angis",
    "all_files": "Tous les fichiers",
    "text_files": "Fichiers texte",
    "set_language": "Définir la Langue",
    "choose_language": "Choisissez la langue de l'IDE :",
    "apply": "Appliquer",
    "cancel": "Annuler",
    "loading": "Chargement...",
    "game_over": "Jeu Terminé",
    "canvas_ready": "Canvas prêt",
    "use_wasd": "Utilisez WASD ou les flèches pour vous déplacer",
    "score": "Score",
    "click_or_space": "Cliquez ou appuyez sur Espace pour battre des ailes",
    "click_restart": "Cliquez ou appuyez sur Espace pour redémarrer",
}

_DE_UI = {
    "open": "Öffnen",
    "save": "Speichern",
    "save_as": "Speichern Als",
    "cut": "Ausschneiden",
    "copy": "Kopieren",
    "paste": "Einfügen",
    "run": "Ausführen",
    "close_tab": "Tab Schließen",
    "editor": "Editor",
    "output": "Ausgabe",
    "errors": "Fehler",
    "select_all": "Alles Auswählen",
    "settings": "Einstellungen",
    "language": "Sprache",
    "window_title": "Angis IDE",
    "untitled": "unbenannt",
    "angis_files": "Angis-Dateien",
    "all_files": "Alle Dateien",
    "text_files": "Textdateien",
    "set_language": "Sprache Festlegen",
    "choose_language": "IDE-Sprache wählen:",
    "apply": "Anwenden",
    "cancel": "Abbrechen",
    "loading": "Laden...",
    "game_over": "Spiel Vorbei",
    "canvas_ready": "Leinwand bereit",
    "use_wasd": "Bewege dich mit WASD oder Pfeiltasten",
    "score": "Punktzahl",
    "click_or_space": "Klicke oder drücke Leertaste zum Flattern",
    "click_restart": "Klicke oder drücke Leertaste zum Neustarten",
}


ENGLISH = LangPack(
    code="en",
    name="English",
    print_words={"say", "print", "show", "display", "tell"},
    set_words={"set", "make", "let", "store"},
    math_words={"add", "plus", "sum", "calculate", "subtract", "minus", "multiply", "times", "divide"},
    app_words={"app", "window", "text", "label", "button", "scene", "lobby", "world"},
    game_words={"game", "flappy", "bird"},
    file_words={"attach", "file", "locate", "find"},
    to_prep={"to"},
    equal_prep={"equal", "="},
    for_prep={"for"},
    in_prep={"in", "inside", "from", "of"},
    as_prep={"as"},
    if_word="if",
    else_word="else",
    and_word="and",
    or_word="or",
    not_word="not",
    true_words={"true", "yes", "on"},
    false_words={"false", "no", "off"},
    on_word="on",
    off_word="off",
    switch_word="switch",
    match_word="match",
    case_word="case",
    when_word="when",
    default_word="default",
    otherwise_word="otherwise",
    define_word="define",
    function_word="function",
    return_word="return",
    call_word="call",
    blueprint_word="blueprint",
    create_word="create",
    named_word="named",
    method_word="method",
    phrase_word="phrase",
    command_word="command",
    means_word="means",
    teaching_words={"when i say", "teach", "when i type"},
    repeat_word="repeat",
    times_word="times",
    while_word="while",
    for_each_words={"for each", "foreach", "for every", "for every thing"},
    collect_word="collect",
    get_word="get",
    lambda_word="lambda",
    arrow_word="arrow",
    fn_word="fn",
    into_prep="into",
    try_word="try",
    except_word="except",
    catch_word="catch",
    finally_word="finally",
    with_word="with",
    async_word="async",
    spawn_word="spawn",
    background_word="background",
    await_word="await",
    decorator_char="@",
    yes_words={"yes"},
    no_words={"no"},
    import_word="import",
    python_word="python",
    include_word="include",
    library_word="library",
    pack_word="pack",
    use_word="use",
    show_word="show",
    say_word="say",
    display_word="display",
    tell_word="tell",
    ask_word="ask",
    input_word="input",
    prompt_word="prompt",
    read_word="read",
    raise_word="raise",
    error_word="error",
    assert_word="assert",
    debug_word="debug",
    all_word="all",
    language_word="language",
    true_word="true",
    false_word="false",
)
ENGLISH._ui = dict(_EN_UI)


SPANISH = LangPack(
    code="es",
    name="Español",
    print_words={"decir", "mostrar", "escribir", "imprimir"},
    set_words={"poner", "establecer", "hacer", "guardar", "crear"},
    math_words={"sumar", "mas", "calcular", "restar", "menos", "multiplicar", "por", "dividir", "entre"},
    app_words={"app", "ventana", "texto", "etiqueta", "boton", "escena", "mundo"},
    game_words={"juego", "flappy"},
    file_words={"adjuntar", "archivo", "localizar", "encontrar"},
    to_prep={"a"},
    equal_prep={"igual"},
    for_prep={"para"},
    in_prep={"en", "dentro"},
    as_prep={"como"},
    if_word="si",
    else_word="sino",
    and_word="y",
    or_word="o",
    not_word="no",
    true_words={"verdadero", "si"},
    false_words={"falso", "no"},
    on_word="encendido",
    off_word="apagado",
    switch_word="seleccionar",
    match_word="coincidir",
    case_word="caso",
    when_word="cuando",
    default_word="defecto",
    otherwise_word="otro",
    define_word="definir",
    function_word="funcion",
    return_word="devolver",
    call_word="llamar",
    blueprint_word="plantilla",
    create_word="crear",
    named_word="llamado",
    method_word="metodo",
    phrase_word="frase",
    command_word="comando",
    means_word="significa",
    teaching_words={"cuando digo", "ensenar"},
    repeat_word="repetir",
    times_word="veces",
    while_word="mientras",
    for_each_words={"para cada", "por cada"},
    collect_word="recolectar",
    get_word="obtener",
    lambda_word="lambda",
    arrow_word="flecha",
    fn_word="fn",
    into_prep="en",
    try_word="intentar",
    except_word="excepto",
    catch_word="capturar",
    finally_word="finalmente",
    with_word="con",
    async_word="asincrono",
    spawn_word="lanzar",
    background_word="fondo",
    await_word="esperar",
    decorator_char="@",
    yes_words={"sí"},
    no_words={"no"},
    import_word="importar",
    python_word="python",
    include_word="incluir",
    library_word="libreria",
    pack_word="paquete",
    use_word="usar",
    show_word="mostrar",
    say_word="decir",
    display_word="exhibir",
    tell_word="contar",
    ask_word="preguntar",
    input_word="entrada",
    prompt_word="indicio",
    read_word="leer",
    raise_word="lanzar",
    error_word="error",
    assert_word="afirmar",
    debug_word="depurar",
    all_word="todo",
    language_word="idioma",
    true_word="verdadero",
    false_word="falso",
)
SPANISH._ui = dict(_SP_UI)


FRENCH = LangPack(
    code="fr",
    name="Français",
    print_words={"dire", "montrer", "afficher", "ecrire"},
    set_words={"mettre", "definir", "faire", "stocker"},
    math_words={"ajouter", "plus", "calculer", "soustraire", "moins", "multiplier", "fois", "diviser"},
    app_words={"app", "fenetre", "texte", "label", "bouton", "scene", "monde"},
    game_words={"jeu"},
    file_words={"attacher", "fichier", "localiser", "trouver"},
    to_prep={"a"},
    equal_prep={"egal"},
    for_prep={"pour"},
    in_prep={"dans", "depuis"},
    as_prep={"comme"},
    if_word="si",
    else_word="sinon",
    and_word="et",
    or_word="ou",
    not_word="pas",
    true_words={"vrai", "oui"},
    false_words={"faux", "non"},
    on_word="allume",
    off_word="eteint",
    switch_word="selectionner",
    match_word="correspondre",
    case_word="cas",
    when_word="quand",
    default_word="defaut",
    otherwise_word="autrement",
    define_word="definir",
    function_word="fonction",
    return_word="retourner",
    call_word="appeler",
    blueprint_word="plan",
    create_word="creer",
    named_word="nomme",
    method_word="methode",
    phrase_word="phrase",
    command_word="commande",
    means_word="signifie",
    teaching_words={"quand je dis"},
    repeat_word="repetes",
    times_word="fois",
    while_word="tant",
    for_each_words={"pour chaque"},
    collect_word="collecter",
    get_word="obtenir",
    lambda_word="lambda",
    arrow_word="fleche",
    fn_word="fn",
    into_prep="dans",
    try_word="essayer",
    except_word="sauf",
    catch_word="attraper",
    finally_word="enfin",
    with_word="avec",
    async_word="asynchrone",
    spawn_word="lancer",
    background_word="arriere",
    await_word="attendre",
    decorator_char="@",
    yes_words={"oui"},
    no_words={"non"},
    import_word="importer",
    python_word="python",
    include_word="inclure",
    library_word="bibliotheque",
    pack_word="paquet",
    use_word="utiliser",
    show_word="montrer",
    say_word="dire",
    display_word="afficher",
    tell_word="raconter",
    ask_word="demander",
    input_word="entree",
    prompt_word="invite",
    read_word="lire",
    raise_word="leve",
    error_word="erreur",
    assert_word="affirmer",
    debug_word="deboguer",
    all_word="tout",
    language_word="langue",
    true_word="vrai",
    false_word="faux",
)
FRENCH._ui = dict(_FR_UI)


GERMAN = LangPack(
    code="de",
    name="Deutsch",
    print_words={"sagen", "zeigen", "drucken", "ausgeben"},
    set_words={"setzen", "mache", "lasse", "speichere"},
    math_words={"addieren", "plus", "rechne", "subtrahieren", "minus", "multiplizieren", "mal", "dividieren", "durch"},
    app_words={"app", "fenster", "text", "label", "knopf", "szene", "welt"},
    game_words={"spiel"},
    file_words={"anhangen", "datei", "finden", "lokalisieren"},
    to_prep={"zu"},
    equal_prep={"gleich"},
    for_prep={"fur"},
    in_prep={"in"},
    as_prep={"als"},
    if_word="wenn",
    else_word="sonst",
    and_word="und",
    or_word="oder",
    not_word="nicht",
    true_words={"wahr", "ja"},
    false_words={"falsch", "nein"},
    on_word="an",
    off_word="aus",
    switch_word="umschalten",
    match_word="ubereinstimmen",
    case_word="fall",
    when_word="wenn",
    default_word="standard",
    otherwise_word="andernfalls",
    define_word="definiere",
    function_word="funktion",
    return_word="ruckgabe",
    call_word="rufe",
    blueprint_word="bauplan",
    create_word="erstellen",
    named_word="genannt",
    method_word="methode",
    phrase_word="satz",
    command_word="befehl",
    means_word="bedeutet",
    teaching_words={"wenn ich sage"},
    repeat_word="wiederhole",
    times_word="male",
    while_word="solange",
    for_each_words={"fur jedes"},
    collect_word="sammle",
    get_word="bekomme",
    lambda_word="lambda",
    arrow_word="pfeil",
    fn_word="fn",
    into_prep="in",
    try_word="versuche",
    except_word="ausser",
    catch_word="fange",
    finally_word="schlieszlich",
    with_word="mit",
    async_word="asynchron",
    spawn_word="erzeuge",
    background_word="hintergrund",
    await_word="warte",
    decorator_char="@",
    yes_words={"ja"},
    no_words={"nein"},
    import_word="importieren",
    python_word="python",
    include_word="einschlieszen",
    library_word="bibliothek",
    pack_word="paket",
    use_word="benutze",
    show_word="zeige",
    say_word="sage",
    display_word="ausgeben",
    tell_word="erzahlen",
    ask_word="frage",
    input_word="eingabe",
    prompt_word="aufforderung",
    read_word="lesen",
    raise_word="erhebe",
    error_word="fehler",
    assert_word="behaupten",
    debug_word="debuggen",
    all_word="alle",
    language_word="sprache",
    true_word="wahr",
    false_word="falsch",
)
GERMAN._ui = dict(_DE_UI)


_ACTIVE = ENGLISH


def set_language(lang: str | LangPack) -> None:
    global _ACTIVE
    if isinstance(lang, LangPack):
        _ACTIVE = lang
    else:
        for pack in [ENGLISH, SPANISH, FRENCH, GERMAN]:
            if pack.code == lang or pack.name.lower() == lang.lower():
                _ACTIVE = pack
                return
        raise ValueError(f"Unsupported language: {lang!r}")


def get_language() -> LangPack:
    return _ACTIVE


def _(key: str) -> str:
    return _ACTIVE.ui(key)


def get_supported_languages() -> list[dict[str, str]]:
    return [
        {"code": p.code, "name": p.name}
        for p in [ENGLISH, SPANISH, FRENCH, GERMAN]
    ]
