import json
import os
from elftools.elf.elffile import ELFFile
import struct
from PIL import Image

# Paths
JSON_FILE = "dex/sprites.json"
ELF_FILE = "pokeemerald-test.elf"
OUTPUT_DIR = "dex/sprites"


def read_data_from_elf(elf_file, address, size):
    """Extract binary data from an ELF file at a specified address"""
    with open(elf_file, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            sec_addr = section["sh_addr"]
            sec_size = section["sh_size"]

            # Check if the address falls within this section
            if sec_addr <= address < sec_addr + sec_size:
                offset = address - sec_addr
                data = section.data()
                return data[offset : offset + size]

    return None


def decompress_lz77(data):
    """Decompress LZ77 compressed data"""
    if data[0] != 0x10:  # LZ77 compression identifier
        print("Data does not appear to be LZ77 compressed")
        return data

    decompressed_size = data[1] | (data[2] << 8) | (data[3] << 16)
    result = bytearray()
    pos = 4  # Skip header

    while len(result) < decompressed_size and pos < len(data):
        flags = data[pos]
        pos += 1

        for bit in range(8):
            if flags & (0x80 >> bit):
                if pos + 1 >= len(data):
                    break

                byte1 = data[pos]
                byte2 = data[pos + 1]
                pos += 2

                disp = ((byte1 & 0x0F) << 8) | byte2
                length = ((byte1 >> 4) & 0x0F) + 3

                # Safety check to avoid index errors
                if disp >= len(result):
                    print(
                        f"Displacement {disp} exceeds result size {len(result)}"
                    )
                    continue

                # Copy bytes from already decompressed data
                for i in range(length):
                    if len(result) > 0:
                        result.append(result[-disp - 1])
            else:
                if pos >= len(data):
                    break
                result.append(data[pos])
                pos += 1

            if len(result) >= decompressed_size:
                break

    return bytes(result)


def parse_pointer(ptr_str):
    """Parse a pointer string to an integer address"""
    if isinstance(ptr_str, str):
        # Remove quotes and 0x prefix if present
        ptr_str = ptr_str.strip("\"'")
        if ptr_str.startswith("0x"):
            ptr_str = ptr_str[2:]
        return int(ptr_str, 16)
    return ptr_str


def extract_palette(elf_file, palette_ptr, num_colors=16):
    """Extract and parse a palette from the ELF file with proper GBA color format"""
    # Debug the actual address being used
    print(f"Reading palette from address: 0x{palette_ptr:08X}")

    # Read the palette data - potentially compressed
    raw_data = read_data_from_elf(
        elf_file, palette_ptr, 256
    )  # Larger buffer for compressed data
    if not raw_data:
        print(f"Failed to read palette data at 0x{palette_ptr:X}")
        return None

    # Check if palette is LZ77 compressed
    palette_data = raw_data
    if raw_data[0] == 0x10:  # LZ77 compression identifier
        print("Palette is LZ77 compressed, decompressing...")
        try:
            palette_data = decompress_lz77(raw_data)
            print(f"Decompressed palette size: {len(palette_data)} bytes")
        except Exception as e:
            print(f"Error decompressing palette: {e}")
            return None

    # Parse the palette into RGB values (16 colors, 2 bytes each = 32 bytes)
    palette = []
    for i in range(0, min(32, len(palette_data)), 2):
        if i + 1 < len(palette_data):
            color = struct.unpack("<H", palette_data[i : i + 2])[0]
            r = ((color >> 0) & 0x1F) * 8
            g = ((color >> 5) & 0x1F) * 8
            b = ((color >> 10) & 0x1F) * 8
            palette.append((r, g, b))

    return palette


def render_sprite(sprite_data, palette, width=64, height=64):
    """Render a GBA 4bpp sprite with proper tile ordering"""
    # Create a new image with transparency
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()

    # Verify we have enough data
    expected_size = (width * height) // 2  # 4bpp = 2 pixels per byte
    if len(sprite_data) < expected_size:
        print(
            f"Sprite data too small ({len(sprite_data)} bytes, expected {expected_size})"
        )

    # GBA 4bpp format uses interleaved bit planes
    # Tiles are 8x8 and ordered left-to-right, top-to-bottom
    tile_width = 8
    tile_height = 8
    tiles_per_row = width // tile_width

    # Process each 8x8 tile
    for tile_y in range(height // tile_height):
        for tile_x in range(width // tile_width):
            # Calculate tile index and tile data offset
            tile_index = tile_y * tiles_per_row + tile_x
            tile_offset = tile_index * (
                tile_width * tile_height // 2
            )  # 32 bytes per tile

            # Skip if beyond data
            if tile_offset >= len(sprite_data):
                continue

            # Process each row in the tile
            for row in range(tile_height):
                row_offset = tile_offset + (row * tile_width // 2)

                # Process each column pair (4 bits per pixel = 2 pixels per byte)
                for col_pair in range(tile_width // 2):
                    if row_offset + col_pair >= len(sprite_data):
                        continue

                    # Get byte containing two pixels
                    pixel_byte = sprite_data[row_offset + col_pair]

                    # Extract the two 4-bit pixels (lower 4 bits = first pixel, upper 4 bits = second pixel)
                    # GBA actually has the low nibble as the left pixel
                    pixel1_idx = pixel_byte & 0x0F
                    pixel2_idx = (pixel_byte >> 4) & 0x0F

                    # Calculate coordinates in the final image
                    x1 = tile_x * tile_width + col_pair * 2
                    x2 = x1 + 1
                    y = tile_y * tile_height + row

                    # Set pixels (palette index 0 is transparent)
                    if pixel1_idx > 0 and pixel1_idx < len(palette):
                        pixels[x1, y] = palette[pixel1_idx] + (255,)

                    if pixel2_idx > 0 and pixel2_idx < len(palette):
                        pixels[x2, y] = palette[pixel2_idx] + (255,)

    return image


def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "front"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "front_shiny"), exist_ok=True)

    # Load the sprite data from JSON
    with open(JSON_FILE, "r") as f:
        sprites = json.load(f)

    pokemon_name = "All"  # Set to a specific name to process just one Pokemon

    # Process each Pokemon
    for pokemon in sprites:
        # Skip entries without required data
        if "index" not in pokemon or "speciesName" not in pokemon:
            continue

        index = pokemon["index"]
        name = pokemon["speciesName"]

        if pokemon_name != "All" and name != pokemon_name:
            continue

        print(f"Processing {name} (#{index})...")

        # Get sprite and palette pointers
        sprite_ptr = parse_pointer(pokemon.get("frontSprite pointer"))
        normal_palette_ptr = parse_pointer(pokemon.get("normalPalette pointer"))
        shiny_palette_ptr = parse_pointer(pokemon.get("shinyPalette pointer"))

        if not sprite_ptr:
            print(f"  No sprite pointer found for {name}")
            continue

        if not normal_palette_ptr:
            print(f"  No palette pointer found for {name}")
            continue

        # Extract sprite data
        max_sprite_size = 8192  # Little sanity here
        sprite_data = read_data_from_elf(ELF_FILE, sprite_ptr, max_sprite_size)

        if not sprite_data:
            print(f"  Failed to read sprite data for {name}")
            continue

        # Check if sprite is compressed
        is_compressed = sprite_data[0] == 0x10
        if is_compressed:
            try:
                sprite_data = decompress_lz77(sprite_data)
                print(f"  Decompressed sprite data: {len(sprite_data)} bytes")
            except Exception as e:
                print(f"  Error decompressing sprite: {e}")
                continue

        # Extract and parse normal palette
        normal_palette = extract_palette(ELF_FILE, normal_palette_ptr)
        if not normal_palette:
            print(f"  Failed to extract normal palette for {name}")
            continue

        # dimension for the regular sprite
        width = height = 64  # Default size
        single_frame_size = (width * height) // 2  # 4bpp

        # Render and save sprites
        normal_image = render_sprite(
            sprite_data[:single_frame_size], normal_palette, width, height
        )
        normal_output_path = os.path.join(OUTPUT_DIR, "front", f"{index}.png")
        normal_image.save(normal_output_path)
        print(f"  Saved normal sprite to {normal_output_path}")

        # Prepare anim directories
        anim_front_dir = os.path.join(OUTPUT_DIR, "anim_front")
        anim_front_shiny_dir = os.path.join(OUTPUT_DIR, "anim_front_shiny")
        os.makedirs(anim_front_dir, exist_ok=True)
        os.makedirs(anim_front_shiny_dir, exist_ok=True)

        # Handle animation frame for normal
        if len(sprite_data) >= single_frame_size * 2:
            anim_frame_data = sprite_data[single_frame_size : single_frame_size * 2]
            anim_image = render_sprite(anim_frame_data, normal_palette, width, height)
            anim_output_path = os.path.join(anim_front_dir, f"{index}.png")
            anim_image.save(anim_output_path)
            print(f"  Saved anim frame to {anim_output_path}")
        else:
            # Copy regular frame to anim directory
            anim_output_path = os.path.join(anim_front_dir, f"{index}.png")
            normal_image.save(anim_output_path)
            print(f"  Copied normal frame to anim directory: {anim_output_path}")

        # Process shiny palette if available
        if shiny_palette_ptr:
            shiny_palette = extract_palette(ELF_FILE, shiny_palette_ptr)
            if shiny_palette:
                shiny_image = render_sprite(
                    sprite_data[:single_frame_size], shiny_palette, width, height
                )
                shiny_output_path = os.path.join(
                    OUTPUT_DIR, "front_shiny", f"{index}.png"
                )
                shiny_image.save(shiny_output_path)
                print(f"  Saved shiny sprite to {shiny_output_path}")

                # Handle animation frame for shiny
                if len(sprite_data) >= single_frame_size * 2:
                    anim_frame_data = sprite_data[
                        single_frame_size : single_frame_size * 2
                    ]
                    anim_shiny_image = render_sprite(
                        anim_frame_data, shiny_palette, width, height
                    )
                    anim_shiny_output_path = os.path.join(
                        anim_front_shiny_dir, f"{index}.png"
                    )
                    anim_shiny_image.save(anim_shiny_output_path)
                    print(f"  Saved shiny anim frame to {anim_shiny_output_path}")
                else:
                    # Copy regular shiny frame to anim directory
                    anim_shiny_output_path = os.path.join(
                        anim_front_shiny_dir, f"{index}.png"
                    )
                    shiny_image.save(anim_shiny_output_path)
                    print(
                        f"  Copied shiny frame to anim directory: {anim_shiny_output_path}"
                    )


if __name__ == "__main__":
    main()
