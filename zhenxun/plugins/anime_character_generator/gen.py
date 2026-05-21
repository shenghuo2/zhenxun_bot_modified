import asyncio

from dotenv import load_dotenv
from novelai_python import ApiCredential, GenerateImageInfer, ImageGenerateResp
from novelai_python.sdk.ai.generate_image import Model, Sampler, UCPreset
from pydantic import SecretStr

load_dotenv()
session = ApiCredential(
    api_token=SecretStr(
        "pst-V7xHX4Kf55ryIqLS6y1qk9uYF1Cpd9hkN3R0UWGf52GZ5YMaezX4ptkqiNYexpuV"
    )
)  # pst-***
# For security reasons, storing user credentials in plaintext is strongly discouraged.

prompt = """1 girl, {solo}, {official art},simple background, {full body},standing,



loli, long_hair, brown_eyes, flat_chest, aqua_hair, long_pointy_ears, shackles, denim_shorts, three_strand_braid

, hair_flaps, chef"""


async def main():
    gen = GenerateImageInfer.build_generate(
        prompt=prompt,
        model=Model.NAI_DIFFUSION_4_5_CURATED,
        sampler=Sampler.K_EULER_ANCESTRAL,
        ucPreset=UCPreset.TYPE0,
        # Recommended, using preset negative_prompt depends on selected model
        qualityToggle=True,
        decrisp_mode=False,
        variety_boost=True,
        furry_mode=False,
        # Checkbox in novelai.net
    )
    cost = gen.calculate_cost(is_opus=True)
    print(f"charge: {cost} if you are vip3")
    resp = await gen.request(session=session)
    resp: ImageGenerateResp
    print(resp.meta)
    file = resp.files[0]
    with open(file[0], "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
