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

import unittest

from cloudify.state import current_ctx
from cloudify.mocks import (
    MockCloudifyContext,
    MockNodeContext,
    MockNodeInstanceContext,
    MockRelationshipContext,
    MockRelationshipSubjectContext
)
from cloudify_ip_booking import tasks
from cloudify_ip_booking.constants import (
    AVAILABLE_IPV4,
    AVAILABLE_IPV6,
    RESERVATIONS_PROPERTY
)


class TestTasks(unittest.TestCase):
    def _mock_resource_ip_reservation_ctx(self):
        properties = {
            'resource_config': [
                '10.0.1.0/24',
                '10.0.2.0/24',
                '10.0.3.0/24'
            ]
        }

        ctx = MockCloudifyContext(
            node_id='test_reservation',
            node_type='cloudify.nodes.ip_booking.IpReservation',
            properties=properties
        )

        current_ctx.set(ctx)
        return ctx

    def _mock_resource_ipv6_reservation_ctx(self):
        properties = {
            'resource_config': [
                '2001:db8:100::/40'
            ]
        }

        ctx = MockCloudifyContext(
            node_id='test_reservation',
            node_type='cloudify.nodes.ip_booking.IpReservation',
            properties=properties
        )

        current_ctx.set(ctx)
        return ctx

    def _mock_resource_del_ctx(self):
        ctx = MockCloudifyContext(
            node_id='test_reservation',
            node_type='cloudify.nodes.ip_booking.IpReservation',
            runtime_properties={AVAILABLE_IPV4: ['0.0.0.0/0'],
                                AVAILABLE_IPV6: ['::/0']}
        )

        current_ctx.set(ctx)
        return ctx

    def _mock_free_ip_rel_ctx(self):
        available_v4 = [
            '128.0.0.0/1', '64.0.0.0/2', '16.0.0.0/4', '0.0.0.0/5',
            '32.0.0.0/3', '12.0.0.0/6', '8.0.0.0/7', '11.0.0.0/8',
            '10.128.0.0/9', '10.64.0.0/10', '10.32.0.0/11', '10.16.0.0/12',
            '10.8.0.0/13', '10.4.0.0/14', '10.2.0.0/15', '10.1.0.0/16',
            '10.0.8.0/21', '10.0.4.0/22', '10.0.128.0/17', '10.0.0.16/28',
            '10.0.2.0/23', '10.0.64.0/18', '10.0.0.12/30', '10.0.1.0/24',
            '10.0.0.11/32', '10.0.32.0/19', '10.0.0.128/25', '10.0.0.32/27',
            '10.0.0.64/26', '10.0.16.0/20', '10.0.0.0/32'
        ]

        # target
        tar_rel_subject_ctx = MockRelationshipSubjectContext(
            node=MockNodeContext(
                id='test_reservation',
                type='cloudify.nodes.ip_booking.IpReservation',
                properties={
                    'resource_config': [available_v4]
                }
            ),
            instance=MockNodeInstanceContext(
                id='test_reservation_123456',
                runtime_properties={
                    AVAILABLE_IPV4: available_v4,
                    AVAILABLE_IPV6: ['::/0'],
                    RESERVATIONS_PROPERTY: {'test_item_123456': '10.0.0.2'}
                }
            )
        )

        rel_ctx = MockRelationshipContext(
            type='cloudify.relationships.ip_booking.reserve_ip_item',
            target=tar_rel_subject_ctx
        )

        # source
        src_ctx = MockCloudifyContext(
            node_id='test_item_123456',
            node_type='cloudify.nodes.ip_booking.IpItem',
            source=self,
            target=tar_rel_subject_ctx,
            relationships=rel_ctx
        )

        current_ctx.set(src_ctx)
        return src_ctx

    def _mock_resource_free_ip(self):
        properties = {
            'resource_config': [
                '10.0.1.0/24',
                '10.0.2.0/24',
                '10.0.3.0/24'
            ]
        }

        ctx = MockCloudifyContext(
            node_id='test_reservation',
            node_type='cloudify.nodes.ip_booking.IpReservation',
            properties=properties
        )

        current_ctx.set(ctx)
        return ctx

    def _mock_resource_list_item_ctx(self):
        ctx = MockCloudifyContext(
            node_id='test_item',
            node_type='cloudify.nodes.ip_booking.IpItem'
        )

        current_ctx.set(ctx)
        return ctx

    def _mock_reserve_ip_item_rel_ctx(self):
        # target
        tar_rel_subject_ctx = MockRelationshipSubjectContext(
            node=MockNodeContext(
                id='test_reservation',
                type='cloudify.nodes.ip_booking.IpReservation',
                properties={
                    'resource_config': []
                }
            ),
            instance=MockNodeInstanceContext(
                id='test_reservation_123456',
                runtime_properties={
                    AVAILABLE_IPV4: ['0.0.0.0/0'],
                    AVAILABLE_IPV6: ['::/0']
                }
            )
        )

        rel_ctx = MockRelationshipContext(
            type='cloudify.relationships.resources.reserve_ip',
            target=tar_rel_subject_ctx
        )

        # source
        src_ctx = MockCloudifyContext(
            node_id='test_item_123456',
            node_type='cloudify.nodes.ip_booking.IpItem',
            source=self,
            target=tar_rel_subject_ctx,
            relationships=rel_ctx
        )
        current_ctx.set(src_ctx)
        return src_ctx

    def test_create_ip_reservation(self):
        ctx = self._mock_resource_ip_reservation_ctx()

        # when (create)
        tasks.create_ip_pool(ctx)

        # then (create)
        self.assertTrue(
            AVAILABLE_IPV4 in ctx.instance.runtime_properties)
        self.assertTrue(
            AVAILABLE_IPV6 in ctx.instance.runtime_properties)

        self.assertEqual(
            ctx.instance.runtime_properties[AVAILABLE_IPV4],
            [
                '10.0.1.0/24',
                '10.0.2.0/24',
                '10.0.3.0/24'
            ]
        )

        self.assertEqual(
            ctx.instance.runtime_properties[AVAILABLE_IPV6],
            ['::/0']
        )

    def test_create_ipv6_reservation(self):
        ctx = self._mock_resource_ipv6_reservation_ctx()

        # when (create)
        tasks.create_ip_pool(ctx)

        # then (create)
        self.assertTrue(
            AVAILABLE_IPV4 in ctx.instance.runtime_properties)

        self.assertTrue(
            AVAILABLE_IPV6 in ctx.instance.runtime_properties)

        self.assertEqual(
            ctx.instance.runtime_properties[AVAILABLE_IPV4],
            ['0.0.0.0/0']
        )

        self.assertEqual(
            ctx.instance.runtime_properties[AVAILABLE_IPV6],
            ['2001:db8:100::/40']
        )

    def test_delete_resources_list(self):
        ctx = self._mock_resource_del_ctx()

        # when (delete)
        tasks.delete_ip_pool(ctx)

        # then (delete)
        self.assertNotIn(AVAILABLE_IPV4, ctx.instance.runtime_properties)
        self.assertNotIn(AVAILABLE_IPV6, ctx.instance.runtime_properties)

    def test_reserve_ip(self):
        ctx = self._mock_reserve_ip_item_rel_ctx()

        # when (reserve)
        tasks.reserve_ip(ctx, ip='10.0.1.0/24')

        # then (reserve)
        self.assertEqual(
            len(ctx.target.instance.runtime_properties[AVAILABLE_IPV4]),
            24
        )

    def test_free_ip(self):
        ctx = self._mock_free_ip_rel_ctx()

        # when (return)
        tasks.free_ip(ctx)

        # then (return)
        self.assertEqual(
            len(ctx.target.instance.runtime_properties[AVAILABLE_IPV4]),
            32
        )

        self.assertEqual(
            ctx.target.instance.runtime_properties[AVAILABLE_IPV6],
            ['::/0']
        )

    def test_reserve_ip_range(self):
        ctx = self._mock_reserve_ip_item_rel_ctx()

        # when (reserve)
        tasks.reserve_ip_range(ctx,
                               from_ip='10.0.0.1',
                               to_ip='10.0.0.10')

        # then (reserve)
        self.assertEqual(
            len(ctx.target.instance.runtime_properties[AVAILABLE_IPV4]),
            31
        )

    def test_free_ip_range(self):
        ctx = self._mock_free_ip_rel_ctx()

        # when (return)
        tasks.free_ip_range(ctx,
                            from_ip='10.0.0.1',
                            to_ip='10.0.0.10')

        # then (return)
        self.assertEqual(
            ctx.target.instance.runtime_properties[AVAILABLE_IPV4],
            ['0.0.0.0/0']
        )

        self.assertEqual(
            ctx.target.instance.runtime_properties[AVAILABLE_IPV6],
            ['::/0']
        )
