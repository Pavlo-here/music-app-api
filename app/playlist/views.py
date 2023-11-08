"""
Views for the playlist APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Playlist,
    Tag,
    Song,
)
from playlist import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma separated list of IDs to filter",
            ),
            OpenApiParameter(
                "songs",
                OpenApiTypes.STR,
                description="Comma separated list of IDs to filter",
            ),
        ]
    )
)
class PlaylistViewSet(viewsets.ModelViewSet):
    """View for manage playlist APIs."""
    serializer_class = serializers.PlaylistDetailSerializer
    queryset = Playlist.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integer"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve playlists for authenticated user."""
        tags = self.request.query_params.get('tags')
        songs = self.request.query_params.get('songs')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if songs:
            song_ids = self._params_to_ints(songs)
            queryset = queryset.filter(songs__id__in=song_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PlaylistSerializer
        elif self.action == 'upload_image':
            return serializers.PlaylistImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new playlist."""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload image to playlist."""
        playlist = self.get_object()
        serializer = self.get_serializer(playlist, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT, enum=[0, 1],
                description="Filter by items assigned to playlists.",
            ),
        ]
    )
)
class BasePlaylistAttrViewSet(mixins.DestroyModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    """Base viewset of playlist attrs"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get("assigned_only", 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(playlist__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class TagViewSet(BasePlaylistAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class SongViewSet(BasePlaylistAttrViewSet):
    """Manage songs in the database."""
    serializer_class = serializers.SongSerializer
    queryset = Song.objects.all()
