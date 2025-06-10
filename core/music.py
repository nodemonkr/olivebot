import discord
from discord import app_commands
import os


def setup(bot):

    @bot.tree.command(name="들어와", description="봇을 현재 유저의 음성 채널로 호출합니다.")
    async def 들어와(interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("먼저 음성 채널에 접속해주세요.",
                                                    ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

        if vc and vc.channel == voice_channel:
            await interaction.response.send_message("이미 해당 채널에 연결되어 있습니다.",
                                                    ephemeral=True)
        elif vc:
            await vc.move_to(voice_channel)
            await interaction.response.send_message("🔄 다른 채널로 이동했습니다.")
        else:
            await voice_channel.connect()
            await interaction.response.send_message("✅ 음성 채널에 연결되었습니다.")

    @bot.tree.command(name="재생", description="업로드된 파일을 고음질로 재생합니다.")
    @app_commands.describe(filename="듣고싶은 파일",
                           skip_seconds="시작할 위치 (초 단위, 기본 0)")
    async def 재생(interaction: discord.Interaction,
                 filename: str,
                 skip_seconds: int = 0):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("먼저 음성 채널에 접속해주세요.",
                                                    ephemeral=True)
            return

        filepath = f"./{filename}"
        if not os.path.isfile(filepath):
            await interaction.response.send_message(
                f"❌ `{filename}` 파일이 존재하지 않습니다.", ephemeral=True)
            return

        try:
            vc = await interaction.user.voice.channel.connect()
        except discord.ClientException:
            vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

        if not vc:
            await interaction.response.send_message("봇이 음성 채널에 연결되지 못했습니다.",
                                                    ephemeral=True)
            return

        vc.stop()
        ffmpeg_audio = discord.FFmpegPCMAudio(
            filepath,
            before_options=f"-ss {skip_seconds}",
            options="-vn -ac 2 -f s16le -ar 48000 -b:a 192k")
        vc.play(ffmpeg_audio)
        await interaction.response.send_message(
            f"🎵 `{filename}` 파일을 {skip_seconds}초부터 고음질로 재생합니다.")

    @bot.tree.command(name="정지", description="현재 재생 중인 음악을 정지합니다.")
    async def 정지(interaction: discord.Interaction):
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏹️ 음악이 정지되었습니다.")
        else:
            await interaction.response.send_message("재생 중인 음악이 없습니다.",
                                                    ephemeral=True)

    @bot.tree.command(name="나가", description="봇이 음성 채널에서 나갑니다.")
    async def 나가(interaction: discord.Interaction):
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("👋 봇이 음성 채널에서 나갔습니다.")
        else:
            await interaction.response.send_message("봇이 현재 음성 채널에 없습니다.",
                                                    ephemeral=True)
