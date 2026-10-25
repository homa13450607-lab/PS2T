###############################################################
# PS2T - Persian Speech To Text
#
# Transcription API Endpoint
#
# Version: 2.1.0
#
# Responsibility:
#
#   - Receive audio/video file
#   - Create transcription job
#   - Process background task
#   - Return result
#
###############################################################


import uuid
import asyncio

from pathlib import Path


from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)


from fastapi.responses import FileResponse



from app.core.config import settings


from app.core.job_manager import (
    job_manager,
    JobStatus
)



from app.core.ffmpeg_utils import (
    extract_audio_to_wav
)



from app.core.logger import (
    app_logger,
    error_logger
)



from app.engines.manager import (
    speech_engine_manager
)



from app.dictionary.processor import (
    DictionaryProcessor
)



from app.export.txt_exporter import (
    TxtExporter
)



from app.export.word_exporter import (
    WordExporter
)





###############################################################
# Router
###############################################################


router = APIRouter()





###############################################################
# Dictionary
###############################################################


dict_processor = DictionaryProcessor()






###############################################################
# Background Job Processor
###############################################################


async def process_job_background(

        job_id: str,

        input_file_path: Path

):


    try:


        #######################################################
        # Step 1
        # Extract Audio
        #######################################################


        job_manager.update_progress(

            job_id,

            10,

            JobStatus.PROCESSING

        )




        wav_path = (

            settings.temp_dir

            /

            f"{job_id}.wav"

        )





        app_logger.info(

            f"Extracting audio: {input_file_path.name}"

        )





        loop = asyncio.get_running_loop()



        extracted = await loop.run_in_executor(

            None,

            extract_audio_to_wav,

            input_file_path,

            wav_path

        )





        if not extracted:


            job_manager.fail_job(

                job_id,

                "FFmpeg audio extraction failed"

            )


            return







        #######################################################
        # Step 2
        # Prepare Dictionary Prompt
        #######################################################


        initial_prompt = ""



        if settings.dictionary_enabled:


            initial_prompt = (

                dict_processor
                .get_initial_prompt()

            )









        #######################################################
        # Step 3
        # Speech Engine
        #######################################################


        job_manager.update_progress(

            job_id,

            30,

            JobStatus.PROCESSING

        )





        app_logger.info(

            f"Sending job {job_id} to Speech Engine"

        )





        result = await speech_engine_manager.transcribe(

            str(wav_path),

            initial_prompt

        )






        #######################################################
        # Step 4
        # Post Processing
        #######################################################


        result.job_id = job_id






        if settings.dictionary_enabled:



            result.full_text = (

                dict_processor
                .apply_post_processing(

                    result.full_text

                )

            )



            for segment in result.segments:



                segment.text = (

                    dict_processor
                    .apply_post_processing(

                        segment.text

                    )

                )









        #######################################################
        # Step 5
        # Complete Job
        #######################################################


        job_manager.complete_job(

            job_id,

            result

        )





        app_logger.info(

            f"Job completed successfully: {job_id}"

        )








        #######################################################
        # Cleanup
        #######################################################


        if settings.cleanup_temp_files:



            if wav_path.exists():


                wav_path.unlink()






    except Exception as e:



        error_logger.exception(

            f"Job processing failed {job_id}: {e}"

        )



        job_manager.fail_job(

            job_id,

            str(e)

        )








###############################################################
# Upload Endpoint
###############################################################


@router.post(
    "/transcribe"
)
async def create_transcription_job(

        file: UploadFile = File(...)

):



    job_id = str(uuid.uuid4())





    upload_dir = settings.uploads_dir





    extension = (

        Path(file.filename)

        .suffix

        .lower()

    )





    saved_path = (

        upload_dir

        /

        f"{job_id}{extension}"

    )








    ###########################################################
    # Save File
    ###########################################################


    with open(

        saved_path,

        "wb"

    ) as f:



        content = await file.read()


        f.write(content)








    job = job_manager.create_job(

        job_id,

        file.filename

    )







    asyncio.create_task(

        process_job_background(

            job_id,

            saved_path

        )

    )






    return {


        "job_id": job_id,


        "status": job.status,


        "filename": file.filename


    }









###############################################################
# Job Status
###############################################################


@router.get(
    "/jobs/{job_id}"
)
async def get_job_status(

        job_id: str

):



    job = job_manager.get_job(

        job_id

    )





    if not job:



        raise HTTPException(

            status_code=404,

            detail="Job not found"

        )






    return {



        "job_id":

            job.job_id,



        "filename":

            job.filename,



        "status":

            job.status,



        "progress":

            job.progress,



        "result":

            job.result,



        "error":

            job.error_message


    }








###############################################################
# Download Result
###############################################################


@router.get(
    "/download/{job_id}/{export_format}"
)
async def download_result(

        job_id: str,

        export_format: str

):



    job = job_manager.get_job(

        job_id

    )





    if not job or not job.result:



        raise HTTPException(

            status_code=404,

            detail="Result not available"

        )







    safe_name = (

        Path(job.filename)

        .stem

    )







    if export_format == "txt":



        file_path = TxtExporter.export(

            job.result,

            safe_name

        )



        return FileResponse(

            file_path,

            filename=f"{safe_name}.txt",

            media_type="text/plain"

        )







    elif export_format == "docx":



        file_path = WordExporter.export(

            job.result,

            safe_name

        )



        return FileResponse(

            file_path,

            filename=f"{safe_name}.docx",

            media_type=

            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        )








    raise HTTPException(

        status_code=400,

        detail="Invalid export format"

    )