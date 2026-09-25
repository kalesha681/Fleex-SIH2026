from setuptools import find_packages, setup

package_name = 'fleex_communication'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cp-lab',
    maintainer_email='kalesha681@users.noreply.github.com',
    description='FLEEX Communication package for distributed AMRs',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'fleex_heartbeat_publisher = fleex_communication.heartbeat_publisher:main'
        ],
    },
)
