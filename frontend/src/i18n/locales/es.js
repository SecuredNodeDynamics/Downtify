export default {
  language: {
    name: 'Español',
  },
  common: {
    cancel: 'Cancelar',
    save: 'Guardar',
    close: 'Cerrar',
    delete: 'Eliminar',
    refresh: 'Actualizar',
    download: 'Descargar',
    yes: 'Sí',
    no: 'No',
    unknownArtist: 'Artista desconocido',
    unknownTrack: 'Pista desconocida',
    previousPage: 'Página anterior',
    nextPage: 'Página siguiente',
    loading: 'Cargando',
  },
  nav: {
    home: 'Inicio',
    library: 'Biblioteca',
    monitor: 'Monitor',
    health: 'Salud',
    metadata: 'Metadatos',
    queue: 'Cola',
    player: 'Reproductor',
    settings: 'Ajustes',
    search: 'Buscar',
    more: 'Más',
    back: 'Atrás',
    switchToLight: 'Cambiar a claro',
    switchToDark: 'Cambiar a oscuro',
    updateAvailable: 'Actualización disponible — abrir ayuda y actualizaciones',
    downloadCounter: '{count} descargas activas — abrir cola',
  },
  hero: {
    noAccount: 'sin cuenta de Spotify',
    tagline:
      'Tu música con metadatos completos, portada y letras — en un clic.',
    songs: 'Canciones',
    albums: 'Álbumes',
    playlists: 'Listas',
  },
  search: {
    placeholder: 'Busca o pega un enlace de Spotify o YouTube Music…',
    placeholderArtist: 'Busca por nombre de artista',
    placeholderAlbum: 'Busca por nombre de álbum',
    placeholderTrack: 'Busca por nombre de canción',
    libraryPlaceholder: 'Busca tu música descargada…',
    libraryHint:
      'Filtra la cola del reproductor a la música ya en este servidor.',
    title: 'Resultados de búsqueda',
    matchesFor: 'Mostrando coincidencias para',
    resultsCount: '- {count} resultado',
    resultsCountPlural: '- {count} resultados',
    typeToBegin: 'Escribe algo en la barra de búsqueda para empezar.',
    error: 'Algo salió mal.',
    errorWithDetail: 'Algo salió mal: {detail}',
    empty: 'No se encontraron canciones.',
    emptyHint:
      'Prueba con otra búsqueda — artista + título suele funcionar mejor.',
    emptyAlbums: 'No se encontraron álbumes.',
    emptyTracks: 'No se encontraron pistas.',
    emptyFilterHint: 'Prueba cambiar el filtro de arriba a Ambos u otro tipo.',
    filterLabel: 'Tipo de resultado',
    filterBoth: 'Ambos',
    filterAlbums: 'Álbumes',
    filterTracks: 'Pistas',
    openOnSpotify: 'Abrir en Spotify',
    openOnYoutubeMusic: 'Abrir en YouTube Music',
    inQueue: 'En la cola',
    inLibrary: 'En la biblioteca',
    viewInLibrary: 'Ver en la biblioteca',
    viewAlbum: 'Ver album',
    playTrack: 'Reproducir pista',
    download: 'Descargar',
    downloadAlbum: 'Descargar album',
    downloadTrack: 'Descargar pista',
    demo: 'Demo',
    playInEmbed: 'Reproducir vista previa',
    noPreview: 'No hay vista previa de audio para este elemento.',
    previewError: 'No se pudo cargar la vista previa.',
    trackType: 'Pista',
    albumType: 'Album',
    tracksTag: 'Pistas',
    trackCountOne: '{count} pista',
    trackCountMany: '{count} pistas',
    previousPage: 'Página anterior',
    nextPage: 'Página siguiente',
  },
  queue: {
    tab: 'Cola',
    title: 'Cola de descargas',
    subtitle:
      'Canciones que has añadido a la cola. Progreso, estado y acciones rápidas aquí.',
    empty: 'No hay nada en la cola ahora mismo.',
    emptyHint: 'Busca una canción y pulsa descargar para empezar.',
    saveToDevice: 'Guardar en el dispositivo',
    removeFromQueue: 'Quitar de la cola',
    clearAll: 'Limpiar todo',
    clearAllPrompt: '¿Eliminar todos los elementos de la cola?',
    forceAudio: 'Forzar fuente de audio',
    overridePlaceholder: 'Pega una URL de YouTube o YouTube Music…',
    applyOverride: 'Aplicar',
    invalidYouTubeURL: 'URL de YouTube no válida',
  },
  history: {
    tab: 'Historial',
    title: 'Historial de descargas',
    subtitle: 'Intentos recientes de descarga, guardados entre reinicios.',
    empty: 'Aún no hay historial de descargas.',
    emptyHint: 'Las descargas completadas y fallidas aparecerán aquí.',
    done: 'Completada',
    skipped: 'Ya descargada',
    failed: 'Fallida',
    downloading: 'Descargando',
    queued: 'En cola',
    retry: 'Reintentar descarga',
    clear: 'Limpiar historial',
    clearPrompt: '¿Limpiar todo el historial de descargas?',
    downloadFile: 'Descargar archivo',
    openInPlayer: 'Abrir en el reproductor',
    failedLoad: 'No se pudo cargar el historial de descargas.',
    failedRetry: 'No se pudo reintentar esta descarga.',
  },
  failed: {
    tab: 'Fallidas',
    empty: 'No hay descargas fallidas.',
    emptyHint:
      'Las descargas fallidas apareceran aqui con acciones para reintentar o eliminar.',
    delete: 'Eliminar',
    deletePrompt: '¿Quitar "{title}" de las descargas fallidas?',
    failedDelete: 'No se pudo quitar esta descarga fallida.',
  },
  manage: {
    tab: 'Administrar',
    title: 'Administrar biblioteca',
    subtitle: 'Explora tu contenido descargado y elimina lo que ya no quieras.',
    empty: 'Aún no hay contenido descargado.',
    emptyHint:
      'Las canciones descargadas aparecerán aquí cuando agregues algunas.',
    search: 'Filtra tus descargas…',
    noMatches: 'Ningún contenido coincide con tu filtro.',
    artists: 'Artistas',
    albums: 'Álbumes',
    tracks: 'Canciones',
    delete: 'Eliminar de las descargas',
    deletePrompt:
      '¿Eliminar "{title}" de tus descargas? Esto no se puede deshacer.',
    deleteAlbum: 'Eliminar álbum de las descargas',
    deleteAlbumPrompt:
      '¿Eliminar el álbum "{name}" ({count} archivos) de tus descargas? Esto no se puede deshacer.',
    deleteArtist: 'Eliminar todo el contenido de las descargas',
    deleteArtistPrompt:
      '¿Eliminar los {count} archivos de "{name}" de tus descargas? Esto no se puede deshacer.',
    deleting: 'Eliminando…',
    failedLoad: 'No se pudo cargar tu contenido descargado.',
    failedDelete: 'No se pudo eliminar este contenido.',
    albumMeta: '{count} canciones',
    artistMeta: '{tracks} canciones - {albums} álbumes',
    count: '{count} archivo',
    countPlural: '{count} archivos',
    artistCount: '{count} artista',
    artistCountPlural: '{count} artistas',
    albumCount: '{count} álbum',
    albumCountPlural: '{count} álbumes',
    refresh: 'Actualizar',
  },
  health: {
    title: 'Salud',
    subtitle:
      'Estado de ejecución, almacenamiento, herramientas y señales recientes.',
    failedLoad: 'No se pudo cargar el estado.',
    statusOk: 'Downtify está saludable',
    statusAttention: 'Downtify necesita atención',
    version: 'Versión {version}',
    queueTotal: '{count} en cola',
    completed24h: '{count} completadas en 24 h',
    recentFailures: '{count} fallos recientes',
    downloads: 'Descargas',
    mediaSaveLocation: 'Ubicación de guardado de medios',
    containerDownloadLocation: 'Ruta de descargas del contenedor',
    localDownloadLocation: 'Ubicación de descarga de este dispositivo',
    data: 'Datos',
    audioFiles: 'Archivos de audio',
    librarySize: 'Tamaño de biblioteca',
    dataSize: 'Tamaño de datos',
    free: 'Libre',
    used: 'Usado',
    files: 'Archivos',
    tools: 'Herramientas',
    available: 'Disponible',
    missing: 'Falta',
    notDetected: 'No detectado',
    settings: 'Ajustes activos',
    recentHistory: 'Historial reciente',
    latestFive: 'últimos 5',
    noHistory: 'Aún no hay historial.',
  },
  library: {
    title: 'Biblioteca',
    subtitle:
      'Música que ya has descargado. Escucha, descarga otra vez o elimina.',
    empty: 'Aún no hay descargas.',
    emptyHint: 'Encuentra una canción para empezar a llenar tu biblioteca.',
    failedLoad: 'No se pudieron cargar las descargas.',
    failedDelete: 'No se pudo eliminar {file}',
    deletePrompt: '¿Eliminar "{file}"?',
    countOne: '{count} archivo en tu biblioteca',
    countMany: '{count} archivos en tu biblioteca',
    downloadToDevice: 'Descargar al dispositivo',
    deleteFile: 'Eliminar archivo',
    play: 'Reproducir',
    artists: 'Artistas',
    tracks: 'Pistas',
    albums: 'Albumes',
    genres: 'Géneros',
    searchPlaceholder: 'Busca en tu biblioteca o música para descargar…',
    clearSearch: 'Borrar búsqueda',
    noSearchResults: 'No hay coincidencias en tu biblioteca.',
    notInLibrary: 'Aún no está en tu biblioteca',
    notInLibraryHint:
      'Descarga cualquier resultado abajo y aparecerá aquí al terminar.',
    downloadTrack: 'Descargar',
    downloadAlbum: 'Descargar álbum',
    downloadFromLink: 'Descargar desde enlace',
    downloadFromLinkHint:
      'Este enlace aún no está en tu biblioteca. Inicia la descarga ahora.',
    onlineSearchLoading: 'Buscando en línea…',
    onlineSearchEmpty: 'No se encontró nada en línea para esta búsqueda.',
    onlineSearchError:
      'No se pudo buscar en línea. Revisa la conexión con el servidor.',
    onlineSearchMore: '{count} resultados más en la página de búsqueda.',
    artistCount: '{artists} artistas - {albums} albumes - {tracks} pistas',
    artistMeta: '{tracks} pistas - {albums} albumes',
    albumMeta: '{tracks} pistas',
    genreMeta: '{tracks} pistas',
    openArtist: 'Abrir artista',
    openAlbum: 'Abrir album',
    playArtist: 'Reproducir artista',
    playAlbum: 'Reproducir album',
    playGenre: 'Reproducir genero',
    backToArtists: 'Artistas',
    backToAlbums: 'Albumes',
    backToGenres: 'Géneros',
    monitorArtist: 'Monitorear artista',
    monitoringArtist: 'Monitoreando',
    monitorPaused: 'Monitor en pausa',
    monitorArtistPickTitle: 'Elegir artista de Spotify',
    monitorArtistPickSubtitle:
      'Elige el artista de Spotify para vigilar nuevas pistas y álbumes.',
    monitorArtistMatchScore: '{score}% coincidencia de nombre',
    monitorArtistNotFound: 'No se encontró un artista coincidente en Spotify.',
    monitorArtistNotFoundShort: 'No encontrado',
    monitorArtistLookupFailed: 'No se pudo buscar este artista en Spotify.',
    monitorArtistAddFailed: 'No se pudo agregar el artista al monitor.',
  },
  metadata: {
    title: 'Metadatos',
    subtitle:
      'Escanea archivos existentes en el servidor y repara etiquetas con coincidencias de MusicBrainz.',
    metadataTab: 'Metadatos',
    albumImagesTab: 'Album Images',
    artistImagesTab: 'Imagenes de artistas',
    artistRepairTab: 'Reparar artistas',
    jellyfinTab: 'Jellyfin',
    toolsMenu: 'Metadata tools',
    scan: 'Escanear biblioteca',
    scanAll: 'Escanear todo',
    scanning: 'Escaneando biblioteca...',
    scanLimit: 'Archivos a escanear',
    resultLimit: 'Correcciones a mostrar',
    scanned: 'Escaneados',
    matches: 'Coincidencias',
    needsFix: 'Reparar',
    total: 'Archivos totales',
    serverOnly:
      'Esto escanea archivos en la ubicacion de descarga del servidor Downtify. Las carpetas locales del navegador aun no estan disponibles para el backend.',
    empty: 'No se encontraron correcciones de metadatos en este escaneo.',
    matchFound: 'Coincidencia encontrada',
    noMatch: 'Sin coincidencia',
    apply: 'Aplicar correccion',
    repairAll: 'Corregir todo',
    fixAllAlbumImages: 'Fix all album images',
    fixAllArtistImages: 'Corregir todas las imagenes de artistas',
    fixAllArtistTags: 'Corregir todos los artistas',
    fixing: 'Corrigiendo...',
    fixed: 'Corregido',
    completed: 'Completado',
    clean: 'Al día',
    cleanShort: 'Bien',
    listView: 'Vista de lista',
    gridView: 'Vista de tarjetas',
    repairFailed: 'Correccion fallida',
    repairFailedShort: 'Fallido',
    artistImages: 'Imagenes locales de artistas',
    albumImageLimit: 'Album images to show',
    scanAlbumImages: 'Scan album images',
    emptyAlbumImages: 'No album cover fixes found in this scan.',
    emptyAlbumImageCompleted: 'No album image repairs completed yet.',
    emptyAlbumImageClean: 'No album image scan results without repairs yet.',
    failedAlbumImageScan: 'Failed to scan album images.',
    failedAlbumImageApply: 'Failed to repair album image.',
    albumImageRepairOk: 'Album images repaired.',
    albumImageRepairPartial:
      'Repaired {succeeded} of {total} album image items.',
    albumImageRepairProgressDetail:
      'Repairing album images {current}/{total}: {name} - {succeeded} fixed, {failed} failed',
    missingAlbumCover: 'Missing embedded album cover',
    existingAlbumCover: 'Existing embedded cover',
    replaceAlbumCover: 'Replace cover',
    artistImagesSubtitle:
      'Busca carpetas de artistas sin imagen local y guarda arte nuevo como Nombre del artista.jpg/png/webp. Jellyfin puede mostrar arte en cache o de proveedores que no esta guardado en tu carpeta de musica.',
    artistImageLimit: 'Imagenes de artistas para mostrar',
    scanArtistImages: 'Escanear imagenes',
    missingImages: 'Imagenes locales faltantes',
    emptyArtistImages:
      'No se encontraron imagenes locales de artistas faltantes con arte disponible.',
    emptyArtistImageCompleted:
      'Todavia no se completaron correcciones de imagenes de artistas.',
    emptyArtistImageClean:
      'Todavia no hay resultados de imagenes de artistas sin correccion.',
    emptyArtistImageFailed: 'No fallo ninguna correccion de imagen de artista.',
    before: 'Antes',
    after: 'Despues',
    blank: 'Vacio',
    idsOnly:
      'Se pueden agregar IDs de MusicBrainz; las etiquetas visibles ya coinciden.',
    moreChanges: 'cambios de campo mas',
    failedScan: 'No se pudo escanear los metadatos.',
    failedApply: 'No se pudo aplicar la correccion de metadatos.',
    failedArtistImageScan: 'No se pudo escanear imagenes de artistas.',
    failedArtistImageApply: 'No se pudo reparar la imagen del artista.',
    artistTagLimit: 'Reparaciones de artistas para mostrar',
    scanArtistTags: 'Escanear nombres de artistas',
    groupedArtists: 'Artistas agrupados',
    artistTagsHint:
      'Encuentra canciones donde varios artistas estan guardados como un solo nombre y los escribe como etiquetas de artista individuales.',
    currentArtists: 'Artistas actuales',
    proposedArtists: 'Artistas individuales',
    verifiedArtists: 'Artistas verificados',
    fixArtists: 'Corregir artistas',
    emptyArtistTags:
      'No se encontraron etiquetas de artistas agrupados en este escaneo.',
    emptyArtistTagCompleted:
      'Todavia no se completaron reparaciones de etiquetas de artistas.',
    emptyArtistTagClean:
      'Todavia no hay resultados limpios de etiquetas de artistas.',
    failedArtistTagScan: 'No se pudo escanear etiquetas de artistas.',
    failedArtistTagApply: 'No se pudo reparar etiquetas de artistas.',
    artistTagRepairOk: 'Etiquetas de artistas reparadas.',
    artistTagRepairPartial:
      'Se repararon {succeeded} de {total} elementos de etiquetas de artistas.',
    artistTagRepairProgressDetail:
      'Reparando etiquetas de artistas {current}/{total}: {name} · {succeeded} corregidos, {failed} fallidos',
    folderVerification: 'Verificacion de carpetas',
    artistFolderVerified:
      '{created} carpetas individuales de artistas verificadas; {removed} carpetas agrupadas eliminadas.',
    artistFolderVerifiedPartial:
      '{created} carpetas individuales de artistas verificadas; {remaining} carpetas agrupadas todavia contienen archivos.',
    failedVerify:
      'La escritura termino, pero el archivo todavia tiene cambios pendientes.',
    jellyfinTools: 'Herramientas Jellyfin',
    jellyfinToolsSubtitle:
      'Compara los artistas de Jellyfin con carpetas locales y actualiza la biblioteca despues de reparar.',
    reconcileArtists: 'Comparar artistas',
    reconcilingArtists: 'Comparando artistas...',
    reconcilingArtistsHint:
      'Comparando metadatos de artistas de Jellyfin con carpetas locales y etiquetas.',
    refreshJellyfin: 'Actualizar Jellyfin',
    jellyfinReconcileOk: 'Comparacion de artistas completada.',
    jellyfinRefreshOk: 'Actualizacion de Jellyfin iniciada.',
    jellyfinRefreshFailed: 'No se pudo actualizar Jellyfin.',
    jellyfinRepairSyncFailed:
      'Las imagenes locales se repararon, pero fallo la actualizacion o verificacion de Jellyfin.',
    artistImageRepairOk: 'Imagen de artista reparada.',
    artistImageRepairPartial:
      'Se repararon {succeeded} de {total} imágenes de artista. La actualización o verificación de Jellyfin puede seguir pendiente.',
    artistImageRepairProgress:
      'Reparando imágenes de artista ({current}/{total}): {name}',
    artistImageRepairProgressDetail:
      'Reparando {current}/{total}: {name} · {succeeded} guardadas, {failed} fallidas',
    artistImageRepairRefreshing:
      'Imágenes locales guardadas. Actualizando reconciliación de artistas…',
    artistImageRepairSyncWarning:
      'La imagen local se guardó, pero la carga a Jellyfin no se completó.',
    artistReconciliation: 'Comparacion de artistas',
    jellyfinLibrary: 'Biblioteca',
    jellyfinArtists: 'Artistas en Jellyfin',
    localArtistFolders: 'Carpetas locales de artistas',
    missingLocalImages: 'Imagenes locales faltantes',
    localImageReady: 'Arte local listo',
    missingLocalImage: 'Falta arte local',
    applyImage: 'Aplicar imagen',
    chooseCover: 'Elegir portada',
    updateCover: 'Actualizar portada',
    chooseCoverTitle: 'Elegir portada del artista',
    chooseCoverHint:
      'Elige una imagen de YouTube Music, Deezer, Spotify, Discogs, MusicBrainz o Jellyfin.',
    chooseCoverLoading: 'Cargando opciones de portada…',
    chooseCoverLoadingSlow:
      'Aún buscando en YouTube Music, Discogs y MusicBrainz; puede tardar hasta un minuto.',
    chooseCoverPreviewUnavailable: 'Vista previa no disponible',
    chooseCoverEmpty:
      'No se encontraron opciones de portada para este artista.',
    chooseCoverFailed: 'No se pudieron cargar las opciones de portada.',
    applySelectedCover: 'Aplicar portada seleccionada',
    fixFailed: 'Reparación fallida',
    bulkFixGroup: 'Reparar este grupo',
    bulkFixShort: 'Reparar',
    bulkFixAvailable: '{count} se pueden reparar',
    bulkFixReady: '{count} candidatos de imagen reparables en este grupo.',
    bulkFixTagsReady:
      '{count} coincidencias de etiquetas reparables en este grupo.',
    noRepairFile:
      'Ejecuta el escaneo de imagenes de artistas para encontrar una fuente de reparacion.',
    fixTags: 'Reparar etiquetas',
    tagRepairOk: 'Etiquetas de metadata reparadas.',
    tagRepairPartial:
      'Se repararon {succeeded} de {total} elementos de etiquetas.',
    tagRepairProgressDetail:
      'Reparando etiquetas {current}/{total}: {name} · {succeeded} reparadas, {failed} fallidas',
    jellyfinOnly: 'Solo en Jellyfin',
    folderOnly: 'Solo carpeta',
    tagOnly: 'Solo etiquetas locales',
    matchedArtists: 'Coinciden',
    lastChecked: 'Ultima revision',
    notCheckedYet: 'Aun no revisado',
    noArtistsInBucket: 'No hay artistas aqui.',
    emptyReconciliation:
      'Ejecuta la comparacion para revisar artistas de Jellyfin y locales.',
    repairLog: 'Registro de reparaciones',
    emptyRepairLog: 'Aun no hay reparaciones registradas.',
  },
  monitor: {
    title: 'Monitor',
    subtitle:
      'Vigila listas y artistas de Spotify. Las nuevas pistas se descargan automáticamente en cada revisión.',
    watchNew: 'Vigilar algo nuevo',
    typePlaylist: 'Lista',
    typeArtist: 'Artista',
    kindPlaylist: 'Lista',
    kindArtist: 'Artista',
    urlPlaceholderPlaylist: 'Busca listas de Spotify o pega una URL...',
    urlPlaceholderArtist: 'Busca artistas de Spotify o pega una URL...',
    searching: 'Buscando en Spotify...',
    searchFailed:
      'La búsqueda falló. Pega un enlace de Spotify o inténtalo de nuevo.',
    noSearchResults:
      'No se encontraron coincidencias. Prueba con un nombre más específico.',
    selectTarget: 'Seleccionar para vigilar',
    selectedTarget: 'Listo para vigilar',
    clearSearch: 'Limpiar búsqueda',
    watch: 'Vigilar',
    failedAdd: 'No se pudo añadir. Comprueba la URL e inténtalo de nuevo.',
    failedLoad:
      'No se pudieron cargar las listas monitorizadas. Actualiza la página.',
    empty: 'Aún no hay nada vigilado.',
    emptyHint:
      'Pega un enlace de lista o artista de Spotify arriba para empezar.',
    active: 'Activa',
    paused: 'Pausada',
    everyInterval: 'Cada {interval}',
    tracksOne: '{count} pista',
    tracksMany: '{count} pistas',
    checked: 'Revisada {when}',
    notChecked: 'Aún no revisada',
    pause: 'Pausar vigilancia',
    resume: 'Reanudar vigilancia',
    checkNow: 'Revisar ahora',
    checkAll: 'Revisar ahora todos los elementos monitorizados',
    checkFailed: 'Fallo la revision del monitor.',
    stop: 'Dejar de vigilar',
    applyInterval: 'Aplicar',
    failedApplyInterval: 'No se pudo actualizar la frecuencia de revision.',
    failedUpdate: 'No se pudo actualizar la configuracion del monitor.',
    deletePrompt: '¿Dejar de vigilar "{name}"?',
    info: 'Al añadir una lista o artista, Downtify descarga todas las pistas que encuentra y sigue vigilando. Las canciones nuevas en Spotify se detectan y descargan automáticamente en la siguiente revisión.',
    every15: 'Cada 15 min',
    every30: 'Cada 30 min',
    every1h: 'Cada hora',
    every3h: 'Cada 3 h',
    every6h: 'Cada 6 h',
    every12h: 'Cada 12 h',
    every1d: 'Cada día',
    every1w: 'Cada semana',
    every2w: 'Cada 2 semanas',
    every1mo: 'Cada mes',
    short15: '15 min',
    short30: '30 min',
    short1h: '1 h',
    short3h: '3 h',
    short6h: '6 h',
    short12h: '12 h',
    short1d: '1 día',
    short1w: '1 sem',
    short2w: '2 sem',
    short1mo: '1 mes',
    minSuffix: 'min',
    hourSuffix: 'h',
    daySuffix: 'día',
    daysSuffix: 'días',
    weekSuffix: 'semana',
    weeksSuffix: 'semanas',
    monthSuffix: 'mes',
    monthsSuffix: 'meses',
    timeJustNow: 'justo ahora',
    timeMinAgo: 'hace {n} min',
    timeHourAgo: 'hace {n} h',
    timeDayAgo: 'hace {n} día(s)',
  },
  settings: {
    title: 'Ajustes',
    subtitle: 'Ajusta cómo Downtify descarga y etiqueta tu música.',
    generalTab: 'General',
    monitorArtistInitialSearch: 'Primera búsqueda del artista monitorizado',
    monitorArtistInitialSearchHint:
      'Buscar automáticamente álbumes y canciones al monitorizar un artista.',
    apiTab: 'API',
    logsTab: 'Registros',
    aboutTab: 'Acerca',
    helpTab: 'Ayuda',
    logsHint: 'Intentos recientes de reparar metadatos e imagenes de artistas.',
    logsError: 'No se pudieron cargar los registros.',
    aboutTitle: 'Acerca de Downtify',
    aboutSubtitle:
      'Guia rapida de cada pagina y seccion de mantenimiento de la app.',
    aboutSearchTitle: 'Busqueda',
    aboutSearchText:
      'Busca canciones, albumes, listas o pega enlaces de Spotify y YouTube Music. Revisa coincidencias y envia descargas a la cola.',
    aboutLibraryTitle: 'Biblioteca',
    aboutLibraryText:
      'Explora la musica descargada en el servidor, agrupada por artistas y albumes. Sirve para revisar lo que Downtify guardo.',
    aboutQueueTitle: 'Cola y descargas',
    aboutQueueText:
      'Sigue descargas activas, archivos completados, fallos, reintentos y acciones manuales para guardar archivos.',
    aboutPlayerTitle: 'Reproductor',
    aboutPlayerText:
      'Reproduce pistas descargadas dentro de la app con arte, controles de cola, aleatorio, repeticion y volumen.',
    aboutMonitorTitle: 'Monitor',
    aboutMonitorText:
      'Vigila listas y artistas de Spotify. Downtify descarga el catálogo actual y revisa si hay canciones nuevas.',
    aboutMetadataTitle: 'Herramienta de metadatos',
    aboutMetadataText:
      'Escanea archivos del servidor, compara etiquetas locales con MusicBrainz y aplica reparaciones verificadas.',
    aboutArtistImagesTitle: 'Herramienta de imagenes',
    aboutArtistImagesText:
      'Encuentra artistas sin arte local, crea carpetas permitidas y guarda imagenes que Jellyfin puede usar localmente.',
    aboutJellyfinTitle: 'Herramientas Jellyfin',
    aboutJellyfinText:
      'Compara artistas de Jellyfin con carpetas locales y actualiza Jellyfin despues de reparar metadatos o imagenes.',
    aboutHealthTitle: 'Salud',
    aboutHealthText:
      'Revisa estado del backend, rutas de almacenamiento, herramientas, cola, fallos recientes y visibilidad de descargas.',
    aboutSettingsTitle: 'Ajustes',
    aboutSettingsText:
      'Configura proveedores, calidad, letras, organizacion, API de Jellyfin, registros y descargas locales o del servidor.',
    aboutWorkflowTitle: 'Flujo recomendado',
    aboutWorkflowText:
      'Busca y descarga musica, revisa la cola, explora la biblioteca y usa Metadatos e Imagenes antes de actualizar Jellyfin.',
    aboutBack: 'Back to About',
    aboutWhatItDoes: 'What it does',
    aboutTips: 'Tips',
    aboutSearchDetail:
      'Search is the starting point for finding music before it enters your local Downtify library.',
    aboutSearchPoint1:
      'Search by track, artist, album, playlist, or paste a supported Spotify or YouTube Music link.',
    aboutSearchPoint2:
      'Preview results when a preview source is available before adding them to the queue.',
    aboutSearchPoint3:
      'Queue single tracks, whole albums, playlists, or monitored artist catalogs.',
    aboutSearchTip1:
      'Paste direct Spotify links when you want Downtify to preserve better title, artist, album, and cover metadata.',
    aboutSearchTip2:
      'Use specific artist and album names when search results are too broad.',
    aboutLibraryDetail:
      'Library is the main browser for music that already exists in your selected download folder.',
    aboutLibraryPoint1:
      'Browse by artist, album, track, or genre with quick search across downloaded files.',
    aboutLibraryPoint2:
      'Open albums or genres in the Player without returning to Search.',
    aboutLibraryPoint3:
      'Review cover art, track counts, local ownership, and monitor badges.',
    aboutLibraryTip1:
      'Use the refresh button after importing files outside Downtify or after metadata repairs.',
    aboutLibraryTip2:
      'Genre and cover browsing improves as metadata and artist images are repaired.',
    aboutQueueDetail:
      'Queue and downloads shows what Downtify is doing right now and what happened recently.',
    aboutQueuePoint1:
      'Watch pending, active, completed, and failed download jobs.',
    aboutQueuePoint2:
      'Retry failed jobs or clear completed history when the list gets noisy.',
    aboutQueuePoint3:
      'Confirm where downloaded files landed and whether metadata work succeeded.',
    aboutQueueTip1:
      'If repeated failures appear, check Health for missing tools or storage permission issues.',
    aboutQueueTip2:
      'Large playlists may keep working in the background while the app remains open.',
    aboutPlayerDetail:
      'Player turns the downloaded library into a simple local listening experience.',
    aboutPlayerPoint1:
      'Play tracks, albums, artists, genres, or queued library selections.',
    aboutPlayerPoint2:
      'Use shuffle, repeat, next, previous, seek, and volume controls.',
    aboutPlayerPoint3:
      'See now-playing cover art and upcoming tracks from the current playlist.',
    aboutPlayerTip1:
      'If artwork looks wrong, repair metadata or artist images, then refresh the Library.',
    aboutPlayerTip2:
      'On Android, keep storage permission enabled so local playback can read saved files.',
    aboutMonitorDetail:
      'Monitor keeps selected Spotify artists and playlists up to date without requiring manual searches.',
    aboutMonitorPoint1:
      'Add a Spotify artist or playlist URL and choose how often it should be checked.',
    aboutMonitorPoint2:
      'Pause, resume, force-check, change frequency, or remove monitored items.',
    aboutMonitorPoint3:
      'New tracks are added to the download queue when the monitor sees additions.',
    aboutMonitorTip1:
      'Use artist monitoring for catalogs that grow over time and playlist monitoring for curated lists.',
    aboutMonitorTip2:
      'If covers are missing, wait for the image cache or refresh the Monitor page after the backend catches up.',
    aboutMetadataDetail:
      'Metadata repairs help Jellyfin, genre browsing, album grouping, and player displays stay accurate.',
    aboutMetadataPoint1:
      'Scan files for missing or inconsistent title, artist, album, track, date, and genre tags.',
    aboutMetadataPoint2:
      'Compare local metadata against MusicBrainz-style matches before applying changes.',
    aboutMetadataPoint3:
      'Review the repair log to see what changed and whether it succeeded.',
    aboutMetadataTip1:
      'Repair metadata before refreshing Jellyfin so the server imports cleaner information.',
    aboutMetadataTip2:
      'Work in smaller batches when a large library has many uncertain matches.',
    aboutArtistImagesDetail:
      'Artist Images focuses on local artist artwork files, especially for Jellyfin-compatible folder layouts.',
    aboutArtistImagesPoint1:
      'Scan for missing, mismatched, or folder-only artist images.',
    aboutArtistImagesPoint2:
      'Choose local, Jellyfin, MusicBrainz, or remote candidate images.',
    aboutArtistImagesPoint3:
      'Save approved images into artist folders so Library and Jellyfin can reuse them.',
    aboutArtistImagesTip1:
      'A named artist image usually gives better artist cards than album-cover fallbacks.',
    aboutArtistImagesTip2:
      'Refresh Jellyfin after applying images so server-side artwork updates.',
    aboutJellyfinDetail:
      'Jellyfin tools connect Downtify cleanup work to your Jellyfin music server.',
    aboutJellyfinPoint1:
      'Configure Jellyfin URL, API key, and library name in the API tab.',
    aboutJellyfinPoint2:
      'Compare Jellyfin artists with local artist folders and image files.',
    aboutJellyfinPoint3:
      'Trigger Jellyfin refreshes after metadata or image changes.',
    aboutJellyfinTip1:
      'Use the exact Jellyfin music library name when multiple libraries exist.',
    aboutJellyfinTip2:
      'If Jellyfin does not update immediately, check its scan status and cache behavior.',
    aboutHealthDetail:
      'Health is the troubleshooting dashboard for backend, storage, and tool availability.',
    aboutHealthPoint1:
      'Confirm the backend is reachable and serving the expected version.',
    aboutHealthPoint2:
      'Check download directory visibility, queue state, and recent failures.',
    aboutHealthPoint3:
      'See whether required helper tools are available for downloading and conversion.',
    aboutHealthTip1:
      'Start here when downloads fail, files disappear, or the app cannot read the library.',
    aboutHealthTip2:
      'On Android, Health can reveal storage or embedded-server issues quickly.',
    aboutSettingsDetail:
      'Settings controls the defaults Downtify uses for new downloads and integrations.',
    aboutSettingsPoint1:
      'Choose audio format, bitrate, lyrics behavior, and organization rules.',
    aboutSettingsPoint2:
      'Configure download destination behavior for web, server, and Android modes.',
    aboutSettingsPoint3:
      'Set Jellyfin connection details and inspect maintenance logs.',
    aboutSettingsTip1:
      'Changes affect future work; existing files may need Metadata or Artist Images repairs.',
    aboutSettingsTip2:
      'Save settings before leaving the panel so backend behavior updates.',
    aboutWorkflowDetail:
      'This workflow keeps downloads, local tags, cover art, and Jellyfin in sync with fewer surprises.',
    aboutWorkflowPoint1:
      'Search or monitor music, then let the Queue finish downloading.',
    aboutWorkflowPoint2:
      'Browse Library and Player to spot missing tags, genres, or artwork.',
    aboutWorkflowPoint3:
      'Run Metadata and Artist Images repairs, then refresh Jellyfin when local files look right.',
    aboutWorkflowTip1:
      'Treat Jellyfin refresh as the final step after local cleanup.',
    aboutWorkflowTip2:
      'For large libraries, repeat the workflow in small batches.',
    helpTitle: 'Ayuda y actualizaciones',
    helpSubtitle:
      'Revisa la version instalada de Downtify, busca actualizaciones en GitHub y actualiza instalaciones compatibles.',
    currentVersion: 'Version actual',
    latestVersion: 'Ultima version',
    unknownVersion: 'Desconocida',
    checking: 'Revisando...',
    checkUpdates: 'Buscar actualizaciones',
    checkingUpdates: 'Buscando actualizaciones',
    checkingUpdatesHint:
      'Downtify esta consultando la ultima version en GitHub.',
    updateAvailable: 'Actualizacion disponible',
    updateAvailableHint:
      'La version {version} esta disponible en el repositorio GitHub de Downtify.',
    upToDate: 'Downtify esta actualizado',
    upToDateHint: 'No se encontro una version mas nueva en GitHub.',
    updateCheckFailed: 'Fallo la busqueda de actualizaciones',
    updateCheckError: 'No se pudieron buscar actualizaciones.',
    updateApp: 'Actualizar app',
    updatingApp: 'Actualizando…',
    updateInProgress: 'Actualizacion en curso',
    updateInProgressHint:
      'Downtify esta descargando la nueva version y reiniciando. Puede tardar un minuto; manten esta pagina abierta.',
    updateFailed: 'Actualizacion fallida',
    updateWaitTimeout:
      'La actualizacion no termino a tiempo. El contenedor puede seguir reiniciando o la actualizacion pudo fallar. Revisa el host Docker o intentalo de nuevo.',
    updateHint:
      'Las instalaciones Docker se actualizan desde la app si el socket Docker esta montado; la app se reiniciara.',
    updateHintApk:
      'Descarga el APK mas reciente desde GitHub y abre el instalador de Android.',
    updateHintServerBehind:
      'Esta app es mas nueva que el servidor conectado. Despliega la misma version de Downtify en el servidor y vuelve a abrir la app.',
    versionMismatchHint:
      'Esta app es v{app} pero el servidor conectado es v{server}. Downtify usa una sola version en todos lados; actualiza ambos a v{latest}.',
    updateInProgressHintApk:
      'Descargando la actualizacion desde GitHub. El instalador de Android se abrira al terminar.',
    updateApkInstallerOpened:
      'Instalador abierto. Completa la instalacion en tu dispositivo y vuelve a abrir Downtify.',
    updateError: 'No se pudo actualizar Downtify.',
    updateFinished: 'Actualizacion finalizada',
    refreshAfterUpdate:
      'La nueva version esta funcionando. Actualiza esta pagina para cargar la app actualizada.',
    refreshPage: 'Actualizar esta pagina',
    restartRequired: 'Reinicia Downtify para usar la version actualizada.',
    restartScheduled:
      'El reinicio de Docker fue programado. El contenedor se recreara en breve.',
    manualUpdateCommands: 'Ejecuta estos comandos en el host Docker:',
    viewRelease: 'Ver version',
    audioSource: 'Fuente de audio',
    lyricsSource: 'Fuente de letras',
    lyricsHint: 'solo lrclib está activo',
    downloadLyrics: 'Descargar letras',
    downloadLyricsHint:
      'Incrusta letras en los archivos de audio y escribe archivos .lrc',
    lyricsProvider: 'Proveedor',
    format: 'Formato',
    quality: 'Calidad',
    qualityIgnored: 'ignorada (sin pérdidas)',
    metadataSection: 'Metadatos',
    enhanceMetadata: 'Mejorar etiquetas con MusicBrainz',
    enhanceMetadataHint:
      'Despues de resolver una pista, Downtify usa coincidencias confiables de MusicBrainz para mejorar titulo, artista, album y fecha de lanzamiento.',
    artistFolderPolicy: 'Creacion de carpetas de artistas',
    artistFolderPolicyHint:
      'Controla que carpetas de artistas faltantes puede crear la reparacion de imagenes desde los creditos.',
    artistFolderPolicyArtwork: 'Todos los artistas acreditados con arte',
    artistFolderPolicyPrimary: 'Solo artista principal',
    artistFolderPolicyExisting: 'Solo carpetas existentes',
    jellyfinSection: 'API de Jellyfin',
    serverConnectionSection: 'Servidor Downtify',
    serverConnectionHint:
      'Para la app movil, introduce la direccion de tu servidor Downtify: una IP local (con puerto) o una URL publica como un tunel de Cloudflare. Dejalo vacio si usas el navegador en el mismo host que el servidor.',
    modeSection: 'Modo',
    connectionModeDevice: 'Ejecutar en este dispositivo',
    connectionModeServer: 'Conectar a un servidor',
    connectionModeDeviceHint:
      'Downtify se ejecuta totalmente en este dispositivo: la busqueda y las descargas funcionan sin ningun servidor.',
    connectionModeServerHint:
      'Usa un servidor Downtify en tu red o en internet.',
    connectionModeServerConfigHint:
      'Configura la direccion del servidor en Ajustes → API.',
    runningOnThisDevice: 'Ejecutandose en este dispositivo',
    runningOnThisDeviceHint:
      'La busqueda, las descargas y la conversion ocurren localmente. No se envia nada a un servidor Downtify externo.',
    runningOnThisDeviceSwitchHint:
      'Para conectar a un servidor, cambia a «Conectar a un servidor» en Ajustes generales.',
    serverRequiredTitle: 'Conecta tu servidor Downtify',
    serverRequiredHint:
      'La app movil necesita la direccion del servidor antes de cargar cola, salud y otros datos. Abre Ajustes → API e introduce tu IP local o URL del tunel.',
    serverUrl: 'Direccion del servidor',
    serverUrlPlaceholder: 'https://downtify.ejemplo.com o 192.168.1.50:8765',
    serverUrlCurrent: 'Conectado a',
    serverUrlDefault: 'Esta pagina (mismo host)',
    serverTest: 'Probar conexion',
    serverTesting: 'Probando…',
    serverTestSuccess: 'Conectado a Downtify v{version}',
    serverTestFailed: 'No se pudo alcanzar el servidor Downtify',
    serverInvalidUrl: 'Introduce una URL valida o host:puerto.',
    serverSave: 'Guardar direccion',
    serverConnectDevice: 'Conectar a este dispositivo',
    serverClear: 'Borrar servidor guardado',
    serverSaveHint:
      'Usa Conectar a este dispositivo si ya estas navegando Downtify en el servidor. Para un servidor remoto, introduce su IP o URL del tunel y pulsa Guardar direccion. La app se recarga al conectar.',
    enableJellyfinTools: 'Activar herramientas Jellyfin',
    enableJellyfinToolsHint:
      'Muestra las herramientas de comparacion y actualizacion de Jellyfin en Metadatos.',
    jellyfinUrl: 'URL de Jellyfin',
    jellyfinUrlPlaceholder: 'http://10.128.1.30:8096',
    jellyfinUrlHint:
      'URL base de tu servidor Jellyfin. No incluyas /web al final.',
    jellyfinApiKey: 'Clave API de Jellyfin',
    jellyfinApiKeyPlaceholder: 'Pega la clave API',
    jellyfinApiKeyHint:
      'Se usara luego para sincronizar la biblioteca Jellyfin y actualizar imagenes de artistas.',
    jellyfinTest: 'Probar',
    jellyfinTesting: 'Probando...',
    jellyfinTestSuccess: 'Conexion correcta. La clave API es valida.',
    jellyfinTestFailed: 'Fallo la prueba de conexion',
    jellyfinMusicLibrary: 'Biblioteca o carpeta de musica',
    jellyfinMusicLibraryPlaceholder: 'Seleccionar biblioteca',
    jellyfinMusicLibraryHint:
      'Nombre o ruta de la biblioteca de musica de Jellyfin que Downtify debe escanear/sincronizar.',
    jellyfinLibraryLoading: 'Cargando bibliotecas...',
    jellyfinNoLibraries:
      'No se encontraron bibliotecas de musica. Verifica tu URL de Jellyfin y clave API.',
    jellyfinLibraryError: 'Error al cargar las bibliotecas',
    playlistsSection: 'Listas',
    generateM3u: 'Generar archivo M3U para las listas',
    generateM3uHint:
      'Escribe Playlists/<nombre>.m3u junto a las pistas, tanto para descargas manuales como para los barridos del Monitor.',
    organizationSection: 'Organización de archivos',
    organizeByArtist: 'Organizar por artista',
    organizeByArtistHint:
      'Guarda las canciones en subcarpetas con el nombre del artista. Las pistas de listas también se guardan en la carpeta del artista en lugar de la carpeta de la lista.',
    organizeByAlbum: 'Organizar por álbum',
    organizeByAlbumHint:
      'Requiere organizar por artista. Guarda cada canción en una subcarpeta de álbum dentro de la carpeta del artista (Artista/Álbum/canción).',
    parallelDownloads: 'Descargas paralelas',
    parallelDownloadsHint:
      'Número máximo de canciones descargadas simultáneamente. Valores más altos son más rápidos pero consumen más ancho de banda.',
    saved: 'Cambios guardados',
    saveError: 'No se pudieron guardar los ajustes.',
    language: 'Idioma',
    languageHint: 'Elige el idioma de la interfaz',
    downloadDestination: 'Ubicación de descarga',
    downloadDestinationServer: 'Servidor',
    downloadDestinationLocal: 'Este dispositivo',
    downloadDestinationServerHint:
      'Los archivos permanecen en el servidor de Downtify. Puedes reproducirlos en el reproductor integrado y guardar copias manualmente desde la cola.',
    serverMediaLocation: 'Ubicación de medios del servidor',
    serverMediaLocationPlaceholder: '/mnt/media/Music',
    serverMediaLocationHint:
      'Ruta del servidor que se muestra para tu biblioteca. En Docker, usa la ruta del host montada en /downloads; Downtify escribe mediante el montaje del contenedor.',
    downloadDestinationLocalHint:
      'Cuando termine una descarga, Downtify guardará una copia en la carpeta que elijas en este dispositivo.',
    downloadDestinationBrowserHint:
      'Cuando termine una descarga, Downtify guardara una copia en la ubicacion de descarga seleccionada en tu navegador.',
    downloadDestinationDeviceHint:
      'Cuando termine una descarga, Downtify guardara una copia en la carpeta que elijas en este dispositivo.',
    deviceDownloadsHint:
      'Elige cualquier carpeta de tu dispositivo o tarjeta SD. Toca «Cambiar carpeta…» para elegir donde se guardan las descargas.',
    localFolderLabel: 'Guardar descargas en',
    localFolderNone: 'Aun no se ha seleccionado ninguna carpeta',
    localFolderNameHint:
      'El navegador solo muestra el nombre de la carpeta, no la ruta completa en tu equipo.',
    changeLocalFolder: 'Cambiar carpeta…',
    browserDownloadsHint:
      'Firefox y los navegadores sin acceso a carpetas usan la ubicacion de descarga seleccionada en la configuracion del navegador.',
    localFolderUnsupported:
      'Guardar en una carpeta especifica de este dispositivo requiere Chrome, Edge o Brave. Otros navegadores usan su carpeta de descargas.',
    localFolderInsecure:
      'Elegir carpeta requiere una conexión segura. Abre Downtify en http://localhost o http://127.0.0.1 en lugar de una dirección de red, o usa HTTPS.',
    localFolderPermissionNeeded:
      'El acceso a la carpeta expiró. Haz clic en “Cambiar carpeta…” para permitir guardar de nuevo.',
    localFolderError: 'No se pudo acceder a la carpeta elegida.',
    downloadLocation: 'Ubicación de descargas',
    downloadLocationHint:
      'Las descargas se guardan aquí y la Biblioteca y el Reproductor leen de esta carpeta. De forma predeterminada van a la biblioteca de música de tu dispositivo.',
    deviceLocationDefault: 'Biblioteca de música (predeterminada)',
    chooseFolder: 'Elegir carpeta…',
    useMusicLibrary: 'Usar biblioteca de música',
    deviceStoragePermission:
      'Permite el acceso al almacenamiento para que Downtify pueda guardar y leer esta carpeta.',
    deviceLocationNoPath:
      'Esa carpeta no se puede usar directamente. Elige una carpeta en el almacenamiento interno o en tu tarjeta SD.',
    deviceLocationError: 'No se pudo establecer la ubicación de descargas.',
    deviceFormatNoFfmpeg:
      'Esta versión no tiene un convertidor en el dispositivo, así que las descargas se guardan como M4A (AAC). MP3 y FLAC requieren una versión con ffmpeg.',
  },
  player: {
    title: 'Reproductor',
    subtitle: 'Escucha la música que has descargado.',
    empty: 'Nada que reproducir aún',
    emptyHint: 'Descarga música para empezar a escuchar.',
    queue: 'Cola',
    play: 'Reproducir',
    pause: 'Pausar',
    previous: 'Anterior',
    next: 'Siguiente',
    shuffle: 'Aleatorio',
    shuffleOn: 'Aleatorio activado',
    shuffleOff: 'Aleatorio desactivado',
    repeatOff: 'Repetición desactivada',
    repeatAll: 'Repetir todo',
    repeatOne: 'Repetir una',
    lyrics: 'Letras',
    lyricsOffset: 'Tiempo de letras',
    lyricsEarlier: 'Mostrar letras antes',
    lyricsLater: 'Mostrar letras después',
    lyricsReset: 'Restablecer tiempo de letras',
    volume: 'Volumen',
    mute: 'Silenciar',
    unmute: 'Activar sonido',
    nowPlaying: 'Sonando ahora',
    upNext: 'A continuación',
    queueEmpty: 'No hay otras pistas en esta cola.',
    playFromLibrary: 'Abrir en el reproductor',
    playAll: 'Reproducir todo',
    countOne: '{count} pista',
    countMany: '{count} pistas',
    browse: 'Explorar',
    genres: 'Generos',
    genresShort: 'Generos',
    unknownGenre: 'Genero desconocido',
    genreMeta: '{count} pistas',
    artistBrowseCount: '{count} artistas',
    albumBrowseCount: '{count} albumes',
    genreBrowseCount: '{count} generos',
    noFilterResults: 'Ninguna pista descargada coincide con tu búsqueda.',
    clearFilter: 'Quitar filtro',
    browseSearchPlaceholder: 'Buscar artistas, álbumes, pistas, géneros…',
    detailsEmpty:
      'Los detalles del artista y del álbum aparecen aquí mientras suena una pista.',
    similarArtists: 'Artistas similares',
    similarArtistsEmpty: 'No se encontraron artistas similares.',
    similarMedia: 'Contenido similar',
    similarTracksEmpty: 'No se encontraron pistas similares.',
    trackDetails: 'Detalles de la pista',
    releaseYear: 'Año de lanzamiento',
    durationLabel: 'Duración',
    queuePosition: 'Posición en la cola',
    albumCompleteness: '{have} de {total} pistas en la biblioteca',
    albumMissingShort: 'Faltan {count}',
    albumComplete: 'Completo',
    matchingAlbums: 'Álbumes coincidentes',
    viewAlbumTracks: 'Pistas',
    albumDownloaded: 'Álbum descargado',
    albumNotDownloaded: 'No está en la biblioteca',
    albumTracksOwnedSummary: '{have} de {total} pistas descargadas',
    albumTracksMissingSummary: 'Faltan {count}',
    missingTrack: 'Falta',
    albumTracksUnavailable: 'No se pudieron cargar las pistas de este álbum.',
    downloadAlbum: 'Descargar álbum',
    downloadMissing: 'Descargar faltantes',
    downloadMissingAlbum: 'Descargar pistas faltantes del álbum',
    noMatchingAlbums: 'No se encontraron álbumes en línea coincidentes.',
    openSource: 'Abrir fuente',
    artistAvailableMusic: 'Álbumes y pistas disponibles',
    artistMusicEmpty: 'No se encontró música descargable para este artista.',
    nothingPlaying: 'Nada en reproducción',
    nothingPlayingHint:
      'Elige una pista de tu biblioteca para empezar a escuchar.',
    seek: 'Buscar posición',
  },
  footer: {
    tagline: 'Descargador de música de código abierto',
    updateAvailable: 'Actualización disponible',
  },
}
