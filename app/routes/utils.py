# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Shared route utilities for the classifieds Flask app.

This module contains shared utility functions for use by multiple route Blueprints.
Utilities include image/thumbnail processing and ACID file operations for atomic
database/filesystem commits.
"""

from flask import Blueprint, current_app
from PIL import Image

utils_bp = Blueprint("utils", __name__)


def create_thumbnail(image_path, thumbnail_path):
    """
    Create a thumbnail from an image file.

    Args:
        image_path (str): Path to the original image
        thumbnail_path (str): Path where the thumbnail will be saved
        size (tuple): Thumbnail size (width, height)

    Returns:
        bool: True if thumbnail was created successfully, False otherwise
    """
    size = current_app.config["THUMBNAIL_SIZE"]

    try:
        with Image.open(image_path) as img:
            # Convert palette images (P mode) with transparency to RGBA
            if img.mode == "P":
                img = img.convert("RGBA")
            # For all other images, convert to RGB if not already RGBA/RGB
            elif img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGB")

            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Create a new image with the exact size and paste the thumbnail centered
            thumbnail = Image.new("RGB", size, color="white")

            # Calculate position to center the thumbnail
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2

            thumbnail.paste(img, (x, y))

            # Save the thumbnail
            thumbnail.save(thumbnail_path, "JPEG", quality=85)
            return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False


def move_image_files_to_temp(images, upload_dir, thumbnail_dir, temp_dir):
    """
    Move image files and their thumbnails to temp directory.

    This implements the first step of the temp→commit→cleanup pattern for
    atomic file operations. Files are moved (not copied) to enable rollback
    if database commit fails.

    Args:
        images: List of ListingImage objects to move
        upload_dir: Source directory for image files
        thumbnail_dir: Source directory for thumbnail files
        temp_dir: Destination temp directory

    Returns:
        tuple: (file_moves, success, error_message)
            - file_moves: List of tuples (orig_path, temp_path, orig_thumb, temp_thumb)
            - success: Boolean indicating if all moves succeeded
            - error_message: String with error details if success=False, None otherwise
    """
    import os
    import shutil

    file_moves = []

    for image in images:
        orig_path = os.path.join(upload_dir, image.filename)
        temp_path = os.path.join(temp_dir, image.filename)
        orig_thumb = None
        temp_thumb = None

        if image.thumbnail_filename:
            orig_thumb = os.path.join(thumbnail_dir, image.thumbnail_filename)
            temp_thumb = os.path.join(temp_dir, image.thumbnail_filename)

        try:
            # Move image file if it exists
            if os.path.exists(orig_path):
                shutil.move(orig_path, temp_path)
            else:
                temp_path = None  # Mark as not moved

            # Move thumbnail if it exists
            if orig_thumb and temp_thumb and os.path.exists(orig_thumb):
                shutil.move(orig_thumb, temp_thumb)
            else:
                temp_thumb = None  # Mark as not moved

            file_moves.append((orig_path, temp_path, orig_thumb, temp_thumb))

        except Exception as e:
            # Rollback: restore any files we've moved so far
            restore_files_from_temp(file_moves)
            return [], False, f"Error moving image {image.filename}: {e}"

    return file_moves, True, None


def restore_files_from_temp(file_moves):
    """
    Restore files from temp directory back to original locations (rollback).

    Used when database commit fails and we need to undo file movements.
    This is a best-effort operation - failures are logged but don't raise errors.

    Args:
        file_moves: List of tuples (orig_path, temp_path, orig_thumb, temp_thumb)
                   returned from move_image_files_to_temp()
    """
    import os
    import shutil

    for orig_path, temp_path, orig_thumb, temp_thumb in file_moves:
        # Restore image file
        if temp_path and os.path.exists(temp_path):
            try:
                shutil.move(temp_path, orig_path)
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to restore {orig_path} from temp: {e}"
                )

        # Restore thumbnail
        if temp_thumb and os.path.exists(temp_thumb):
            try:
                shutil.move(temp_thumb, orig_thumb)
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to restore thumbnail {orig_thumb} from temp: {e}"
                )


def cleanup_temp_files(file_moves):
    """
    Delete files from temp directory after successful database commit.

    This is the final step of the temp→commit→cleanup pattern.
    Failures are logged but don't raise errors (best-effort cleanup).

    Args:
        file_moves: List of tuples (orig_path, temp_path, orig_thumb, temp_thumb)
                   returned from move_image_files_to_temp()
    """
    import os

    for orig_path, temp_path, orig_thumb, temp_thumb in file_moves:
        # Delete image from temp
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to delete temp file {temp_path}: {e}"
                )

        # Delete thumbnail from temp
        if temp_thumb and os.path.exists(temp_thumb):
            try:
                os.remove(temp_thumb)
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to delete temp thumbnail {temp_thumb}: {e}"
                )
