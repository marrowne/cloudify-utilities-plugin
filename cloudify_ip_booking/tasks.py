########
# Copyright (c) 2014-2021 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify_ip_booking.ip_reservation import IpReservation

from .constants import (
    AVAILABLE_IPV4,
    AVAILABLE_IPV6,
    RESERVATIONS_PROPERTY,
    RESOURCES_LIST_PROPERTY
)


def _refresh_source_and_target_runtime_props(ctx, **kwargs):
    ctx.source.instance.refresh()
    ctx.target.instance.refresh()


def _update_source_and_target_runtime_props(ctx, **kwargs):
    ctx.source.instance.update()
    ctx.target.instance.update()


@operation(resumable=True)
def create_ip_pool(ctx, **kwargs):
    resource_config = ctx.node.properties.get(RESOURCES_LIST_PROPERTY, [])

    if not isinstance(resource_config, list):
        raise NonRecoverableError(
            'The "resource_config" property must be of type: list')

    ctx.logger.debug('Initializing ip pool...')
    ip_reservation = IpReservation(resource_config)
    ctx.instance.runtime_properties[AVAILABLE_IPV4] = \
        ip_reservation.available_ipv4
    ctx.instance.runtime_properties[AVAILABLE_IPV6] = \
        ip_reservation.available_ipv6


@operation(resumable=True)
def create_ip_item(ctx, **kwargs):
    ctx.logger.debug('Initializing IP item...')


@operation(resumable=True)
def delete_ip_item(ctx, **kwargs):
    ctx.logger.debug('Removing IP item...')


@operation(resumable=True)
def delete_ip_pool(ctx, **kwargs):
    ctx.logger.debug('Removing ip pool:')
    ctx.instance.runtime_properties.pop(AVAILABLE_IPV4, None)
    ctx.instance.runtime_properties.pop(AVAILABLE_IPV6, None)


@operation(resumable=True)
def reserve_ip(ctx, **kwargs):
    ip = kwargs.get('ip')

    if not isinstance(ip, str):
        raise NonRecoverableError(
            'The "ip" parameter must be a string.')

    _refresh_source_and_target_runtime_props(ctx)

    ip_reservation = IpReservation(
        available_v4=ctx.target.instance.runtime_properties[AVAILABLE_IPV4],
        available_v6=ctx.target.instance.runtime_properties[AVAILABLE_IPV6])
    if not ip_reservation.reserve(ip):
        raise NonRecoverableError(
            'Reservation has failed - cannot reserve some addresses in {}.'
            .format(ip))

    ctx.target.instance.runtime_properties[AVAILABLE_IPV4] = \
        ip_reservation.available_ipv4
    ctx.target.instance.runtime_properties[AVAILABLE_IPV6] = \
        ip_reservation.available_ipv6

    reservations = \
        ctx.target.instance.runtime_properties.get(
            RESERVATIONS_PROPERTY, {})
    reservations[ctx.source.instance.id] = ip
    ctx.target.instance.runtime_properties[RESERVATIONS_PROPERTY] = \
        reservations

    _update_source_and_target_runtime_props(ctx)

    ctx.logger.debug('{} reserved successfully.'.format(ip))


@operation(resumable=True)
def free_ip(ctx, **kwargs):
    ip_reservation = IpReservation(
        available_v4=ctx.target.instance.runtime_properties[AVAILABLE_IPV4],
        available_v6=ctx.target.instance.runtime_properties[AVAILABLE_IPV6])

    _refresh_source_and_target_runtime_props(ctx)

    reservations = ctx.target.instance.runtime_properties.get(
        RESERVATIONS_PROPERTY, None)
    if not reservations:
        return ctx.logger.debug('Nothing to do.')

    ip = kwargs.get('ip') or reservations.pop(ctx.source.instance.id)
    if not isinstance(ip, str):
        raise NonRecoverableError(
            'The "resource_config" property must be a string.')

    ctx.logger.debug('Attempting to free ip: {}'.format(ip))

    ip_reservation.free(ip)

    ctx.target.instance.runtime_properties[RESERVATIONS_PROPERTY] = \
        reservations
    ctx.target.instance.runtime_properties[AVAILABLE_IPV4] = \
        ip_reservation.available_ipv4
    ctx.target.instance.runtime_properties[AVAILABLE_IPV6] = \
        ip_reservation.available_ipv6

    _update_source_and_target_runtime_props(ctx)


@operation(resumable=True)
def reserve_ip_range(ctx, **kwargs):
    from_ip = kwargs.get('from_ip')
    to_ip = kwargs.get('to_ip')

    if not isinstance(from_ip, str) or not isinstance(to_ip, str):
        raise NonRecoverableError(
            '"from_ip/to_ip" params must be a string.')

    _refresh_source_and_target_runtime_props(ctx)

    ip_reservation = IpReservation(
        available_v4=ctx.target.instance.runtime_properties[AVAILABLE_IPV4],
        available_v6=ctx.target.instance.runtime_properties[AVAILABLE_IPV6])
    if not ip_reservation.reserve_range(from_ip, to_ip):
        raise NonRecoverableError(
            'Reservation has failed - cannot reserve some addresses in range: '
            '{} - {}.'.format(from_ip, to_ip))

    ctx.target.instance.runtime_properties[AVAILABLE_IPV4] = \
        ip_reservation.available_ipv4
    ctx.target.instance.runtime_properties[AVAILABLE_IPV6] = \
        ip_reservation.available_ipv6

    reservations = \
        ctx.target.instance.runtime_properties.get(
            RESERVATIONS_PROPERTY, {})
    reservations[ctx.source.instance.id] = (from_ip, to_ip)
    ctx.target.instance.runtime_properties[RESERVATIONS_PROPERTY] = \
        reservations

    _update_source_and_target_runtime_props(ctx)

    ctx.logger.debug('Range: {} - {} reserved successfully.'
                     .format(from_ip, to_ip))


@operation(resumable=True)
def free_ip_range(ctx, **kwargs):
    ip_reservation = IpReservation(
        available_v4=ctx.target.instance.runtime_properties[AVAILABLE_IPV4],
        available_v6=ctx.target.instance.runtime_properties[AVAILABLE_IPV6])

    _refresh_source_and_target_runtime_props(ctx)

    reservations = ctx.target.instance.runtime_properties.get(
        RESERVATIONS_PROPERTY, None)
    if not reservations:
        return ctx.logger.debug('Nothing to do.')

    from_ip_ctx, to_ip_ctx = reservations.pop(ctx.source.instance.id)
    from_ip = kwargs.get('from_ip') or from_ip_ctx
    to_ip = kwargs.get('to_ip') or to_ip_ctx
    if not isinstance(from_ip, str) or not isinstance(to_ip, str):
        raise NonRecoverableError(
            '"from_ip/to_ip" params must be a string.')

    ctx.logger.debug('Attempting to free ip range: {} - {}'
                     .format(from_ip, to_ip))

    ip_reservation.free_range(from_ip, to_ip)

    ctx.target.instance.runtime_properties[RESERVATIONS_PROPERTY] = \
        reservations
    ctx.target.instance.runtime_properties[AVAILABLE_IPV4] = \
        ip_reservation.available_ipv4
    ctx.target.instance.runtime_properties[AVAILABLE_IPV6] = \
        ip_reservation.available_ipv6

    _update_source_and_target_runtime_props(ctx)
