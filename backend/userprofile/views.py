from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Profile
from .serializers import UserProfileSerializer


# remember you should be able to edit some user model stuffs from the data in the serializer
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        """
        This view returns the profile of the currently authenticated user.
        """
        user = self.request.user
        return Profile.objects.get(user=user)

    @extend_schema(request_body=UserProfileSerializer)
    def delete(self, request, *args, **kwargs):
        user = request.user

        # Ensure the user is authenticated
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Delete the user's profile and any related data
            profile = user.profile  # The user account is automatically deleted also
            profile.delete()

            return Response(
                {
                    "detail": "Profile deleted successfully. User account is also deleted"
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )
