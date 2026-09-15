#ifndef PROVIDER_H
#define PROVIDER_H

/**
 * @file provider.h
 * @brief Data provider abstraction layer
 */

#include "core/types.h"
#include "data/curl_diagnostics.h"
#include <time.h>
#include <stdbool.h>

typedef enum {
    PROVIDER_CELESTRAK,
    PROVIDER_RETLECTOR,
    PROVIDER_CUSTOM
} ProviderType;

typedef struct {
    char id[16];
    char name[64];
    char base_url[256];
    ProviderType type;
    OrbitalDataFormat default_format;
    bool supports_format[8];
} DataSource;

typedef struct {
    char *data;
    size_t size;
    OrbitalDataFormat format;
    long http_code;
    bool success;
} FetchResult;

typedef struct {
    const char *name;
    bool (*build_url)(const DataSource *source, OrbitalDataFormat format,
                      char *url, size_t url_size);
} DataProvider;

const DataProvider* GetProvider(ProviderType type);

/** fetch data from a source in the specified format.
 *  handles caching internally (120-min TTL).
 *  returns a FetchResult that must be freed with FreeFetchResult(). */
FetchResult FetchFromSource(const DataSource *source, OrbitalDataFormat format);
void FreeFetchResult(FetchResult *result);

/** fetch available groups from retlector.eu API. */
int FetchRetlectorGroups(RetlectorGroup *groups, int max_groups);

/** detect orbital data format from raw content. */
OrbitalDataFormat DetectDataFormat(const char *data, size_t size);

/** fetch from a custom URL and auto-detect the format. */
FetchResult FetchFromCustomURL(const char *url);

extern const DataSource CELESTRAK_SOURCES[];
extern const int NUM_CELESTRAK_SOURCES;
extern const DataSource RETLECTOR_SOURCES[];
extern const int NUM_RETLECTOR_SOURCES;

#endif // PROVIDER_H
