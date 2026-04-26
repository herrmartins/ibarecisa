from .worship_home import WorshipHomeView
from .song_search_view import SongSearchView
from .add_song import SongAddView
from .song_detail_view import SongDetailView
from .add_song_file import add_song_file
from .song_file_listview import SongFileListView

from .search.composer_list_view import ComposerListView
from .search.song_themes_list_view import ThemeListView
from .service_views import (
    WorshipServiceCreateView,
    WorshipServiceDetailView,
    WorshipServiceDeleteView,
    WorshipServiceDuplicateView,
    WorshipServiceFontScaleView,
    WorshipServiceGenerateProgramView,
    WorshipServiceImportView,
    WorshipServiceListView,
    WorshipServicePdfView,
    WorshipServicePrintView,
    WorshipServiceSongCreateView,
    WorshipServiceSongDeleteView,
    WorshipServiceSongResolveView,
    WorshipServiceSongSyncFromProgramView,
    WorshipServiceUpdateView,
)
from .song_pages import SongCreateView, SongListView
from .catalog_views import WorshipCatalogSettingsView
