/*
 * DJI Thermal SDK API definition.
 *
 * @Copyright (c) 2020 DJI. All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */

#pragma once

#ifndef _DIRP_API_H_
#define _DIRP_API_H_

#include "stdint.h"

#ifdef _WIN32
#define dllexport __declspec(dllexport)
#else
#define dllexport __attribute__ ((visibility("default")))
#endif

#define DIRP_PSEUDO_COLOR_LUT_DEPTH             (256)

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief   Error codes
 * @details Most DIRP functions return 0 on success or one of negative value on failure.
 */
typedef enum
{
    DIRP_SUCCESS                    =   0,      /**<   0: Success (no error) */
    DIRP_ERROR_MALLOC               =  -1,      /**<  -1: Malloc error */
    DIRP_ERROR_POINTER_NULL         =  -2,      /**<  -2: NULL pointer input */
    DIRP_ERROR_INVALID_PARAMS       =  -3,      /**<  -3: Invalid parameters input */
    DIRP_ERROR_INVALID_RAW          =  -4,      /**<  -4: Invalid RAW in R-JPEG */
    DIRP_ERROR_INVALID_HEADER       =  -5,      /**<  -5: Invalid header in R-JPEG */
    DIRP_ERROR_INVALID_CURVE        =  -6,      /**<  -6: Invalid curve LUT in R-JPEG */
    DIRP_ERROR_RJPEG_PARSE          =  -7,      /**<  -7: Parse error for R-JPEG data */
    DIRP_ERROR_SIZE                 =  -8,      /**<  -8: Wrong size input */
    DIRP_ERROR_INVALID_HANDLE       =  -9,      /**<  -9: Invalid handle input */
    DIRP_ERROR_FORMAT_INPUT         = -10,      /**< -10: Wrong input image format */
    DIRP_ERROR_FORMAT_OUTPUT        = -11,      /**< -11: Wrong output image format */
    DIRP_ERROR_UNSUPPORTED_FUNC     = -12,      /**< -12: Unsupported function called */
    DIRP_ERROR_NOT_READY            = -13,      /**< -13: Some preliminary conditions not meet */
    DIRP_ERROR_ACTIVATION           = -14,      /**< -13: SDK activate failed */
    DIRP_ERROR_ADVANCED             = -32,      /**< -32: Advanced error codes which may be smaller than this value */
} dirp_ret_code_e;

/**
 * @brief   Palette types
 * @details There are variety of palette options. Distinct colors are used to show temperature
 *          differences in the thermal image, which are related to grayscale intensity.
 */
typedef enum
{
    DIRP_PSEUDO_COLOR_WHITEHOT = 0,             /**<  0: White Hot */
    DIRP_PSEUDO_COLOR_FULGURITE,                /**<  1: Fulgurite */
    DIRP_PSEUDO_COLOR_IRONRED,                  /**<  2: Iron Red */
    DIRP_PSEUDO_COLOR_HOTIRON,                  /**<  3: Hot Iron */
    DIRP_PSEUDO_COLOR_MEDICAL,                  /**<  4: Medical */
    DIRP_PSEUDO_COLOR_ARCTIC,                   /**<  5: Arctic */
    DIRP_PSEUDO_COLOR_RAINBOW1,                 /**<  6: Rainbow 1 */
    DIRP_PSEUDO_COLOR_RAINBOW2,                 /**<  7: Rainbow 2 */
    DIRP_PSEUDO_COLOR_TINT,                     /**<  8: Tint */
    DIRP_PSEUDO_COLOR_BLACKHOT,                 /**<  9: Black Hot */
    DIRP_PSEUDO_COLOR_NUM,                      /**< 10: Total number */
} dirp_pseudo_color_e;

typedef enum
{
    DIRP_VERBOSE_LEVEL_NONE = 0,                /**< 0: Print none */
    DIRP_VERBOSE_LEVEL_DEBUG,                   /**< 1: Print debug log */
    DIRP_VERBOSE_LEVEL_DETAIL,                  /**< 2: Print all log */
    DIRP_VERBOSE_LEVEL_NUM,                     /**< 3: Total number */
} dirp_verbose_level_e;

#pragma pack(push, 1)

/**
 * @brief   API version structure definition.
 */
typedef struct
{
    uint32_t api;                               /**< Version number of this API */
    char     magic[8];                          /**< Magic version of this API */
} dirp_api_version_t;

/**
 * @brief   R-JPEG version structure definition
 */
typedef struct
{
    uint32_t rjpeg;                             /**< Version number of the opened R-JPEG itself. */
    uint32_t header;                            /**< Version number of the header data in R-JPEG */
    uint32_t curve;                             /**< Version number of the curve LUT data in R-JPEG */
} dirp_rjpeg_version_t;

/**
 * @brief   The image size structure definition
 * @details The image size is descripted with a rectangle.
 */
typedef struct {
    int32_t width;                              /**< Horizontal size */
    int32_t height;                             /**< Vertical size */
} dirp_resolotion_t;

/**
 * @brief   Isotherm parameters structure definition
 */
typedef struct {
    bool enable;                                /**< Isotherm switch, enable(true) or disable(false) */
    float high;                                 /**< Upper limit. Only effective when isotherm is enabled. */
    float low;                                  /**< Lower limit. Only effective when isotherm is enabled. */
} dirp_isotherm_t;

/**
 * @brief   Color bar parameters structure definition
 */
typedef struct{
    bool manual_enable;                         /**< Color bar mode, manual(true) or automatic(false) */
    float high;                                 /**< Upper limit. Only effective when color bar is in manual mode. */
    float low;                                  /**< Lower limit. Only effective when color bar is in manual mode. */
} dirp_color_bar_t;

/**
* @brief    Pseudo color LUT array structure definition.
*/
typedef struct{
    uint8_t red  [DIRP_PSEUDO_COLOR_NUM][DIRP_PSEUDO_COLOR_LUT_DEPTH];  /**< Red color LUT */
    uint8_t green[DIRP_PSEUDO_COLOR_NUM][DIRP_PSEUDO_COLOR_LUT_DEPTH];  /**< Green color LUT */
    uint8_t blue [DIRP_PSEUDO_COLOR_NUM][DIRP_PSEUDO_COLOR_LUT_DEPTH];  /**< Blue color LUT */
} dirp_isp_pseudo_color_lut_t;

/**
* @brief    Image enhancement parameteres structure definition.
*/
typedef struct
{
    int32_t brightness;                         /**< Brightness level. Value range is [0~100]. Default value is 50. */
} dirp_enhancement_params_t;

/**
* @brief    Customize temperature measurement parameteres structure definition.
*/
typedef struct {
    float distance;                             /**< The distance to the target.
                                                        Value range is [1~25] meters. */
    float humidity;                             /**< The relative humidity of the environment.
                                                        Value range is [20~100] percent. Defualt value is 70%. */
    float emissivity;                           /**< How strongly the target surface is emitting energy as thermal radiation.
                                                        Value range is [0.10~1.00]. */
    float reflection;                           /**< Reflected temperature in Celsius.
                                                        The surface of the target that is measured could reflect the energy
                                                        radiated by the surrounding objects.
                                                        Value range is [-40.0~500.0] */
} dirp_measurement_params_t;

/**
 * @brief       Structure representing a handle on a DIRP instance
 * @details     It is usually originating from @ref dirp_create_from_rjpeg function.
 *              A DIRP handle is used to perform image processing and temperature measurement operations.
 *              When finished a DIRP processing, you should call @ref dirp_destroy function.
 */
typedef void *DIRP_HANDLE;

#pragma pack(pop)

/**
 * 
 * @brief       Create a new DIRP handle with specified R-JPEG binary data
 * @details     The R-JPEG binary data buffer must remain valid until the handle is destroyed.
 *              The DIRP API library will create some alloc buffers for inner usage.
 *              So the application should reserve enough stack size for the library.
 *
 * @param[in]   data                R-JPEG binary data buffer pointer
 * @param[in]   size                R-JPEG binary data buffer size in bytes
 * @param[out]  ph                  DIRP API handle pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_create_from_rjpeg(const uint8_t *data, int32_t size, DIRP_HANDLE *ph);

/**
 * @brief       Destroy the DIRP handle
 *
 * @param[in]   h                   DIRP API handle
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_destroy(DIRP_HANDLE h);

/**
 * @brief       Get API version
 *
 * @param[out]  version             DIRP API version information pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_api_version(dirp_api_version_t *version);

/**
 * @brief       Get R-JPEG version
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  version             R-JPEG version information pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_rjpeg_version(DIRP_HANDLE h, dirp_rjpeg_version_t *version);

/**
 * @brief       Get R-JPEG image resolution information
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  rjpeg_info          R-JPEG basic information pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_rjpeg_resolution(DIRP_HANDLE h, dirp_resolotion_t *resolution);

/**
 * @brief       Get original RAW binary data from R-JPEG
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  raw_image           Original RAW image data buffer pointer
 * @param[in]   size                Original RAW image data buffer size in bytes
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_original_raw(DIRP_HANDLE h, uint16_t *raw_image, int32_t size);

/**
 * @brief       Run ISP algorithm with RAW data in R-JPEG and output RGB pseudo color image
 * @details     The ISP configurable parameters can be modifed by these APIs:
 *                  - @ref dirp_set_enhancement_params
 *                  - @ref dirp_set_isotherm
 *                  - @ref dirp_set_color_bar
 *                  - @ref dirp_set_pseudo_color
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  color_image         Color image data buffer pointer
 * @param[in]   size                Color image data buffer size in bytes.
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_process(DIRP_HANDLE h, uint8_t *color_image, int32_t size);

/**
 * @brief       Run ISP strech algorithm with RAW data in R-JPEG and output FLOAT32 streching image
 * @details     The ISP strech configurable parameters can be modifed by these APIs:
 *                  - @ref dirp_set_enhancement_params
 *                  - @ref dirp_set_isotherm
 *                  - @ref dirp_set_color_bar
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  strech_image        Strech image data buffer pointer
 * @param[in]   size                Strech image data buffer size in bytes.
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_process_strech(DIRP_HANDLE h, float *strech_image, int32_t size);

/**
 * @brief       Measure temperature of whole thermal image with RAW data in R-JPEG
 * @details     Each INT16 pixel value represents ten times the temperature value in Celsius.
 *              In other words, each LSB represents 0.1 degrees Celsius.
 *              The custom measurement parameters can be modifed by this API:
 *                  - @ref dirp_set_measurement_params
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  temp_image          Temperature image data buffer pointer
 * @param[in]   size                Temperature image data buffer size in bytes
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_measure(DIRP_HANDLE h, int16_t *temp_image, int32_t size);

/**
 * @brief       Measure temperature of whole thermal image with RAW data in R-JPEG
 * @details     Each FLOAT32 pixel value represents the real temperature in Celsius.
 *              The custom measurement parameters can be modifed by this API:
 *                  - @ref dirp_set_measurement_params
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  temp_image          Temperature image data buffer pointer
 * @param[in]   size                Temperature image data buffer size in bytes
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_measure_ex(DIRP_HANDLE h, float *temp_image, int32_t size);

/**
 * @brief       Set custom ISP isotherm parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[in]   isotherm            ISP isotherm parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_set_isotherm(DIRP_HANDLE h, const dirp_isotherm_t *isotherm);

/**
 * @brief       Get orignial/custom ISP isotherm parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  isotherm            ISP isotherm parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_isotherm(DIRP_HANDLE h, dirp_isotherm_t *isotherm);

/**
 * @brief       Set custom ISP color bar parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[in]   color_bar           ISP color bar parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_set_color_bar(DIRP_HANDLE h, const dirp_color_bar_t *color_bar);

/**
 * @brief       Get orignial/custom ISP color bar parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  color_bar           ISP color bar parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_color_bar(DIRP_HANDLE h, dirp_color_bar_t *color_bar);

/**
 * @brief       Get adaptive ISP color bar parameters in automatic mode
 * @details     In color bar automatic mode : manual_enable in @ref dirp_color_bar_t is set as false.
 *              The inner ISP algorithm will calculate the best range values for color bar.
 *              Before calling this API you should call @ref dirp_process once at least.
 *              And if any processing or measurement parameters had been changed, you should also
 *              call @ref dirp_process again for getting new color bar adaptive parameters.
 *              In the above calling @ref dirp_process, manual_enable in @ref dirp_color_bar_t
 *              must be set as <b>false</b>.
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  color_bar           ISP color bar parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_color_bar_adaptive_params(DIRP_HANDLE h, dirp_color_bar_t *color_bar);

/**
 * @brief       Set custom ISP pseudo color type
 *
 * @param[in]   h                   DIRP API handle
 * @param[in]   pseudo_color        ISP pseudo color type @ref dirp_pseudo_color_e
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_set_pseudo_color(DIRP_HANDLE h, dirp_pseudo_color_e pseudo_color);

/**
 * @brief       Get orignial/custom ISP pseudo color type
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  pseudo_color        ISP pseudo color type pointer @ref dirp_pseudo_color_e
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_pseudo_color(DIRP_HANDLE h, dirp_pseudo_color_e *pseudo_color);

/**
 * @brief       Get ISP pseudo color LUT
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  pseudo_lut          ISP pseudo color LUT pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_pseudo_color_lut(dirp_isp_pseudo_color_lut_t *pseudo_lut);

/**
 * @brief       Set custom ISP enhancement parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[in]   enhancement_params  ISP enhancement parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_set_enhancement_params(DIRP_HANDLE h, const dirp_enhancement_params_t *enhancement_params);

/**
 * @brief       Get orignial/custom ISP enhancement parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  enhancement_params  ISP enhancement parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_enhancement_params(DIRP_HANDLE h, dirp_enhancement_params_t *enhancement_params);

/**
 * @brief       Set custom temperature measurement parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[in]   measurement_params  Temperature measurement parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_set_measurement_params(DIRP_HANDLE h, const dirp_measurement_params_t *measurement_params);

/**
 * @brief       Get orignial/custom temperature measurement parameters
 *
 * @param[in]   h                   DIRP API handle
 * @param[out]  measurement_params  Temperature measurement parameters pointer
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_get_measurement_params(DIRP_HANDLE h, dirp_measurement_params_t *measurement_params);

/**
 * @brief       Register SDK for the application.
 * @details     User must call this function once at initialize stage. Key string is "DJI_TSDK\0".
 *
 * @param[in]   key                 The key used to register SDK for the application. This can be applied in DJI Develop Center.
 * @return      int                 return code @ref dirp_ret_code_e
 */
dllexport int32_t dirp_register_app(const char *key);

/**
 * @brief       Set log print level
 *
 * @param[in]   level               Log pring level @ref dirp_verbose_level_e
 */
dllexport void dirp_set_verbose_level(dirp_verbose_level_e level);

/**
 * @brief       Set external logger file
 *
 * @param[in]   file_name           File name which save log information. Set it as nullptr if you want print log on console.
 */
dllexport void dirp_set_logger_file(const char *file_name);

#ifdef __cplusplus
}
#endif

#endif /* _DIRP_API_H_ */
