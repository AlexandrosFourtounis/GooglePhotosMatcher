import os
import time
from datetime import datetime
import piexif
from win32_setctime import setctime
from fractions import Fraction
import subprocess
import shutil


# Function to search media associated to the JSON
def searchMedia(path, title, mediaMoved, nonEdited, editedWord):
    """
    Search for media file matching the JSON metadata.
    Tries multiple patterns in order of likelihood.
    """
    original_title = fixTitle(title)
    
    # Check if file has an extension
    if '.' not in original_title:
        return None
    
    name_part = original_title.rsplit('.', 1)[0]
    ext_part = original_title.rsplit('.', 1)[1]
    
    # List of patterns to try, in order of priority
    patterns_to_try = []
    
    # 1. Edited versions with custom suffix (e.g., "photo-editado.jpg")
    patterns_to_try.append((f"{name_part}-{editedWord}.{ext_part}", True))  # True = has original
    
    # 2. Common Google Photos patterns for duplicates
    patterns_to_try.append((f"{name_part}(1).{ext_part}", False))
    
    # 3. Exact match
    patterns_to_try.append((original_title, False))
    
    # 4. Check for numbered duplicates (2) through (10)
    for i in range(2, 11):
        patterns_to_try.append((f"{name_part}({i}).{ext_part}", False))
    
    # 5. Truncated filename (Google Photos sometimes limits to 47 chars)
    if len(name_part) > 47:
        truncated_name = name_part[:47]
        patterns_to_try.append((f"{truncated_name}-{editedWord}.{ext_part}", True))
        patterns_to_try.append((f"{truncated_name}(1).{ext_part}", False))
        patterns_to_try.append((f"{truncated_name}.{ext_part}", False))
        for i in range(2, 11):
            patterns_to_try.append((f"{truncated_name}({i}).{ext_part}", False))
    
    # 6. Check for edited version with default "editado" suffix if custom suffix was provided
    if editedWord != "editado":
        patterns_to_try.append((f"{name_part}-editado.{ext_part}", True))
        if len(name_part) > 47:
            truncated_name = name_part[:47]
            patterns_to_try.append((f"{truncated_name}-editado.{ext_part}", True))
    
    # Try each pattern
    for pattern, has_original in patterns_to_try:
        filepath = os.path.join(path, pattern)
        
        # Skip if this would be a duplicate JSON match
        if pattern.endswith(f"(1).{ext_part}"):
            json_filepath = os.path.join(path, f"{original_title}(1).json")
            if os.path.exists(json_filepath):
                continue
        
        if os.path.exists(filepath):
            # If this is an edited version, move the original to EditedRaw
            if has_original:
                original_filepath = os.path.join(path, original_title)
                if os.path.exists(original_filepath):
                    try:
                        os.replace(original_filepath, os.path.join(nonEdited, original_title))
                    except Exception as e:
                        print(f"Could not move original file {original_title}: {str(e)}")
            
            return pattern
    
    # Last resort: check if filename already processed
    if original_title in mediaMoved:
        return checkIfSameName(original_title, original_title, mediaMoved, 1)
    
    return None


# Suppress incompatible characters while preserving valid ones
def fixTitle(title):
    """
    Remove characters that are invalid in Windows filenames.
    More conservative approach - only removes truly problematic characters.
    """
    # Windows forbidden characters: < > : " / \ | ? *
    # Also remove some other problematic chars
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    result = str(title)
    for char in forbidden_chars:
        result = result.replace(char, '')
    
    # Remove other potentially problematic characters
    # but be more selective to preserve international characters
    result = result.replace('\x00', '')  # null character
    
    # Trim leading/trailing spaces and dots (Windows doesn't allow these at the end)
    result = result.strip(' .')
    
    return result

# Recursive function to search name if its repeated
def checkIfSameName(title, titleFixed, mediaMoved, recursionTime):
    if titleFixed in mediaMoved:
        titleFixed = title.rsplit('.', 1)[0] + "(" + str(recursionTime) + ")" + "." + title.rsplit('.', 1)[1]
        return checkIfSameName(title, titleFixed, mediaMoved, recursionTime + 1)
    else:
        return titleFixed

def createFolders(fixed, nonEdited):
    if not os.path.exists(fixed):
        os.mkdir(fixed)

    if not os.path.exists(nonEdited):
        os.mkdir(nonEdited)

def setWindowsTime(filepath, timeStamp):
    setctime(filepath, timeStamp)  # Set windows file creation time
    date = datetime.fromtimestamp(timeStamp)
    modTime = time.mktime(date.timetuple())
    os.utime(filepath, (modTime, modTime))  # Set windows file modification time

def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number):
    """convert a number to rational
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def set_EXIF(filepath, lat, lng, altitude, timeStamp):
    exif_dict = piexif.load(filepath)

    dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y:%m:%d %H:%M:%S")  # Create date object
    exif_dict['0th'][piexif.ImageIFD.DateTime] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = dateTime

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)


    try:
        exif_dict = piexif.load(filepath)
        lat_deg = to_deg(lat, ["S", "N"])
        lng_deg = to_deg(lng, ["W", "E"])

        exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
        exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
        }

        exif_dict['GPS'] = gps_ifd

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filepath)

    except Exception as e:
        print("Coordinates not settled")
        pass


def set_video_metadata(filepath, lat, lng, altitude, timeStamp):
    """Set metadata for video files using ffmpeg if available"""
    temp_filepath = None  # Initialize to avoid NameError in cleanup
    try:
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            print("ffmpeg not found, skipping video metadata embedding")
            return False
        
        # Create temporary output file
        temp_filepath = filepath + ".tmp"
        
        # Format datetime for video metadata
        dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build ffmpeg command to copy stream without re-encoding and add metadata
        cmd = [
            'ffmpeg', '-i', filepath,
            '-c', 'copy',  # Copy streams without re-encoding
            '-metadata', f'creation_time={dateTime}',
            '-metadata', f'date={dateTime}',
        ]
        
        # Add GPS coordinates as metadata if available (check for non-zero values)
        if lat != 0 and lng != 0:
            cmd.extend([
                '-metadata', f'location={lat:+.6f}{lng:+.6f}/',
                '-metadata', f'location-eng={lat:+.6f}{lng:+.6f}/',
            ])
        
        cmd.extend(['-y', temp_filepath])  # -y to overwrite output file
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Replace original file with the new one
            os.replace(temp_filepath, filepath)
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            # Clean up temp file if it exists
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return False
            
    except subprocess.TimeoutExpired:
        print("ffmpeg timeout")
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return False
    except Exception as e:
        print(f"Error setting video metadata: {str(e)}")
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return False


